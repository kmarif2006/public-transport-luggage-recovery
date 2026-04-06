import os
import uuid
from datetime import datetime, timezone
from bson import ObjectId
from flask import Blueprint, jsonify, request, session
from backend.extensions import mongo

from ..auth.jwt_handler import jwt_required
from ..extensions import socketio
from ..utils import report_to_dict, found_item_to_dict
from ..semantic_matcher import matcher

manager_bp = Blueprint("manager", __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@manager_bp.get("/reports")
@jwt_required(roles=["manager"])
def manager_reports():
    """Return all relevant luggage reports where this manager's depot is on the travel path."""
    manager = mongo.db.users.find_one({"_id": ObjectId(request.user["id"])})
    if not manager or not manager.get("assigned_depot_id"):
        return jsonify({"message": "Official authorization failed: Depot not assigned"}), 403

    depot_id = manager["assigned_depot_id"]

    # Reports are relevant if the bus passed through this depot (Source, Dest, or Route)
    cursor = mongo.db.lost_luggage_reports.find({
        "$or": [
            {"source_depot_id": depot_id},
            {"destination_depot_id": depot_id},
            {"route_depots": depot_id}
        ]
    }).sort("created_at", -1)

    return jsonify({"reports": [report_to_dict(r) for r in cursor]})


@manager_bp.get("/found-luggage")
@jwt_required(roles=["manager"])
def get_found_luggage():
    """Return all found luggage items posted by this depot manager."""
    manager = mongo.db.users.find_one({"_id": ObjectId(request.user["id"])})
    if not manager:
        return jsonify({"message": "Manager not found"}), 404

    depot_id = manager.get("assigned_depot_id")
    cursor = mongo.db.found_luggage.find({"depot_id": depot_id}).sort("created_at", -1)
    return jsonify({"items": [found_item_to_dict(f) for f in cursor]})


@manager_bp.post("/found-luggage")
@jwt_required(roles=["manager"])
def post_found_luggage():
    """Manager registers found luggage. Triggers active AI matching and user notifications."""
    description = request.form.get("description")
    found_date = request.form.get("found_date")  # YYYY-MM-DD

    if not all([description, found_date]):
        return jsonify({"message": "Missing mandatory found item details"}), 400

    if 'photo' not in request.files:
        return jsonify({"message": "Photo evidence is mandatory for found luggage registration"}), 400

    manager = mongo.db.users.find_one({"_id": ObjectId(request.user["id"])})
    depot_id = manager.get("assigned_depot_id")

    photo = request.files['photo']
    if not photo or not allowed_file(photo.filename):
        return jsonify({"message": "Invalid file format for photo evidence"}), 400

    filename = secure_filename(f"found_{uuid.uuid4().hex}_{photo.filename}")
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    photo.save(filepath)
    photo_url = f"/uploads/{filename}"

    found_report = {
        "depot_id": depot_id,
        "description": description.strip(),
        "found_date": found_date,
        "photo_url": photo_url,
        "created_at": datetime.now(timezone.utc),
    }

    result = mongo.db.found_luggage.insert_one(found_report)
    found_id = str(result.inserted_id)

    # ── ACTIVE AI MATCHING ───────────────────────────────────────────────────
    # Search all open lost reports that include this depot in their route
    open_reports_cursor = mongo.db.lost_luggage_reports.find({
        "status": {"$in": ["reported", "under_review"]},
        "$or": [
            {"source_depot_id": depot_id},
            {"destination_depot_id": depot_id},
            {"route_depots": depot_id}
        ]
    })
    open_reports = list(open_reports_cursor)

    notifications_sent = 0
    MATCH_THRESHOLD = 0.45  # 45% combined score triggers a notification

    if open_reports and matcher._model:
        found_item_data = [{
            "found_id": found_id,
            "description": description.strip(),
            "photo_url": photo_url,
            "depot_id": depot_id,
            "found_date": found_date,
        }]

        for report in open_reports:
            route_depots = report.get("route_depots", [])
            if not route_depots:
                route_depots = [report.get("source_depot_id"), report.get("destination_depot_id")]

            matches = matcher.find_matches_advanced(
                report.get("item_description", ""),
                found_item_data,
                route_depots=route_depots,
                threshold=MATCH_THRESHOLD,
            )

            if matches:
                best = matches[0]
                score = best.get("match_score", 0)
                user_id = report.get("user_id")

                # Save notification to DB
                notification = {
                    "user_id": user_id,
                    "report_id": str(report["_id"]),
                    "found_id": found_id,
                    "item_name": report.get("item_name"),
                    "item_description": report.get("item_description"),
                    "match_score": score,
                    "found_description": description.strip(),
                    "found_photo_url": photo_url,
                    "depot_id": depot_id,
                    "found_date": found_date,
                    "read": False,
                    "created_at": datetime.now(timezone.utc),
                }
                notif_result = mongo.db.notifications.insert_one(notification)

                # Emit real-time SocketIO event to the specific user's room
                socketio.emit("match_found", {
                    "notification_id": str(notif_result.inserted_id),
                    "report_id": str(report["_id"]),
                    "item_name": report.get("item_name"),
                    "match_score": score,
                    "found_description": description.strip(),
                    "found_photo_url": photo_url,
                    "depot_id": depot_id,
                    "found_date": found_date,
                    "message": f"🎉 A potential match ({score}%) was found for your '{report.get('item_name')}' at {depot_id} depot!"
                }, room=f"user_{user_id}")

                notifications_sent += 1
                print(f"[AI] Match {score}% found → notified user {user_id} for report {report['_id']}")

    # ── BROADCAST TO MANAGERS IN THIS DEPOT ─────────────────────────────────
    socketio.emit("new_found_item", {
        "item": found_item_to_dict(found_report | {"_id": result.inserted_id}),
        "matches_triggered": notifications_sent
    }, room=f"depot_{depot_id}")

    return jsonify({
        "message": "Found luggage successfully registered in depot ledger",
        "id": found_id,
        "photo_url": photo_url,
        "notifications_sent": notifications_sent
    }), 201


@manager_bp.put("/found-luggage/<item_id>")
@jwt_required(roles=["manager"])
def update_found_luggage(item_id):
    """Update description of a found luggage item."""
    data = request.get_json() or {}
    new_description = data.get("description", "").strip()
    if not new_description:
        return jsonify({"message": "Description is required"}), 400

    manager = mongo.db.users.find_one({"_id": ObjectId(request.user["id"])})
    depot_id = manager.get("assigned_depot_id")

    try:
        result = mongo.db.found_luggage.update_one(
            {"_id": ObjectId(item_id), "depot_id": depot_id},
            {"$set": {"description": new_description, "updated_at": datetime.now(timezone.utc)}}
        )
        if result.matched_count == 0:
            return jsonify({"message": "Item not found or unauthorized"}), 404
        return jsonify({"message": "Item updated successfully"}), 200
    except Exception as e:
        return jsonify({"message": f"Update failed: {str(e)}"}), 500


@manager_bp.delete("/found-luggage/<item_id>")
@jwt_required(roles=["manager"])
def delete_found_luggage(item_id):
    """Delete a found luggage entry from the depot ledger."""
    manager = mongo.db.users.find_one({"_id": ObjectId(request.user["id"])})
    depot_id = manager.get("assigned_depot_id")

    try:
        result = mongo.db.found_luggage.delete_one(
            {"_id": ObjectId(item_id), "depot_id": depot_id}
        )
        if result.deleted_count == 0:
            return jsonify({"message": "Item not found or unauthorized"}), 404
        return jsonify({"message": "Item removed from depot ledger"}), 200
    except Exception as e:
        return jsonify({"message": f"Deletion failed: {str(e)}"}), 500


@manager_bp.post("/notify-user")
@jwt_required(roles=["manager"])
def notify_user_about_match():
    """Manager notifies user about AI match - sends email notification"""
    data = request.get_json()
    
    report_id = data.get("report_id")
    found_id = data.get("found_id")
    match_score = data.get("match_score")
    
    if not report_id or not found_id:
        return jsonify({"message": "Report ID and Found ID required"}), 400
    
    try:
        # Get the lost report
        report = mongo.db.lost_luggage_reports.find_one({"_id": ObjectId(report_id)})
        if not report:
            return jsonify({"message": "Lost report not found"}), 404
        
        # Get the found item
        found_item = mongo.db.found_luggage.find_one({"_id": ObjectId(found_id)})
        if not found_item:
            return jsonify({"message": "Found item not found"}), 404
        
        # Get user details
        user = mongo.db.users.find_one({"_id": ObjectId(report["user_id"])})
        if not user:
            return jsonify({"message": "User not found"}), 404
        
        # Get depot details
        depot = mongo.db.depots.find_one({"depot_id": found_item["depot_id"]})
        
        # Send email notification
        from .notify_user import send_match_notification_email
        
        match_details = {
            "match_score": f"{match_score}%",
            "found_date": found_item["found_date"],
            "description": found_item["description"],
            "found_id": str(found_item["_id"]),
            "photo_url": found_item.get("photo_url", "")
        }
        
        depot_info = {
            "name": depot["name"] if depot else "Unknown Depot",
            "city": depot["city"] if depot else "Unknown City",
            "district": depot["district"] if depot else "Unknown District",
            "contact_number": depot["contact_number"] if depot else "N/A",
            "manager_email": f"manager.{found_item['depot_id']}@tnstc.gov.in"
        }
        
        success, verification_code = send_match_notification_email(
            user["email"],
            user["name"],
            report["item_name"],
            match_details,
            depot_info
        )
        
        if success:
            # Store notification record
            notification_record = {
                "user_id": str(user["_id"]),
                "report_id": report_id,
                "found_id": found_id,
                "verification_code": verification_code,
                "match_score": match_score,
                "sent_at": datetime.now(timezone.utc),
                "status": "sent",
                "manager_id": str(request.user["id"])
            }
            
            mongo.db.email_notifications.insert_one(notification_record)
            
            return jsonify({
                "success": True,
                "message": f"Email notification sent to {user['email']}",
                "verification_code": verification_code
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Failed to send email notification"
            }), 500
            
    except Exception as e:
        return jsonify({"message": f"Notification failed: {str(e)}"}), 500


@manager_bp.get("/matches/<report_id>")
@jwt_required(roles=["manager"])
def manager_get_matches(report_id):
    """Return AI matches for a specific lost report (manager view)."""
    try:
        report = mongo.db.lost_luggage_reports.find_one({"_id": ObjectId(report_id)})
    except Exception:
        return jsonify({"message": "Invalid report ID"}), 400

    if not report:
        return jsonify({"message": "Report not found"}), 404

    search_depots = report.get("route_depots", [])
    if not search_depots:
        search_depots = [report["source_depot_id"], report["destination_depot_id"]]

    found_cursor = mongo.db.found_luggage.find({
        "depot_id": {"$in": search_depots},
        "found_date": {"$gte": report.get("date_lost", "0000-00-00")}
    })

    found_items = [
        {
            "id": str(f["_id"]),
            "description": f.get("description", ""),
            "photo_url": f.get("photo_url"),
            "depot_id": f.get("depot_id"),
            "found_date": f.get("found_date"),
        }
        for f in found_cursor
    ]

    if not found_items:
        return jsonify({"matches": []})

    matches = matcher.find_matches_advanced(
        report.get("item_description", ""),
        found_items,
        route_depots=search_depots,
        threshold=0.20,
    )
    return jsonify({"matches": matches})


@manager_bp.put("/update-status")
@jwt_required(roles=["manager"])
def update_report_status():
    """Authorized update of lost luggage status with user notification."""
    data = request.get_json() or {}
    report_id = data.get("report_id")
    new_status = data.get("status")

    if not all([report_id, new_status]):
        return jsonify({"message": "report_id and status are required"}), 400

    manager = mongo.db.users.find_one({"_id": ObjectId(request.user["id"])})
    depot_id = manager.get("assigned_depot_id")

    try:
        report = mongo.db.lost_luggage_reports.find_one({"_id": ObjectId(report_id)})
        if not report:
            return jsonify({"message": "Report record not found"}), 404

        is_authorized = (
            report.get("source_depot_id") == depot_id or
            report.get("destination_depot_id") == depot_id or
            depot_id in report.get("route_depots", [])
        )

        if not is_authorized:
            return jsonify({"message": "Unauthorized: This report is not passing through your depot"}), 403

        mongo.db.lost_luggage_reports.update_one(
            {"_id": ObjectId(report_id)},
            {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc)}}
        )

        # Notify the passenger of status change
        status_labels = {
            "reported": "has been reported",
            "under_review": "is Under Review by the depot",
            "found": "has been FOUND! Please contact the depot.",
            "returned": "has been Returned. Case Closed."
        }
        label = status_labels.get(new_status, f"status updated to {new_status}")
        socketio.emit("status_update", {
            "report_id": report_id,
            "new_status": new_status,
            "message": f"📦 Your item '{report.get('item_name')}' {label}"
        }, room=f"user_{report.get('user_id')}")

        return jsonify({"message": f"Status updated to: {new_status}", "status": new_status}), 200
    except Exception as e:
        print(f"[ERROR] Status update failed: {e}")
        return jsonify({"message": "Server error during status update"}), 500
