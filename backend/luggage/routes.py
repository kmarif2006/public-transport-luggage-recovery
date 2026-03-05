import os
import json
import uuid
from datetime import datetime, timezone
from bson import ObjectId
from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename
from thefuzz import fuzz

from ..auth.jwt_handler import jwt_required
from ..extensions import mongo, socketio
from ..semantic_matcher import matcher

luggage_bp = Blueprint("luggage", __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def _report_to_dict(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "user_id": doc.get("user_id"),
        "source_depot_id": doc.get("source_depot_id"),
        "destination_depot_id": doc.get("destination_depot_id"),
        "route_depots": doc.get("route_depots", []),
        "item_name": doc.get("item_name"),
        "item_description": doc.get("item_description"),
        "date_lost": doc.get("date_lost"),
        "bus_number": doc.get("bus_number"),
        "contact_phone": doc.get("contact_phone"),
        "photo_url": doc.get("photo_url"),
        "status": doc.get("status", "reported"),
        "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None,
    }

@luggage_bp.post("/report-luggage")
@jwt_required()
def report_luggage():
    """Create a lost luggage report. Bus number is optional. Matching handles route & dates."""
    source_depot_id = request.form.get("source_depot_id")
    destination_depot_id = request.form.get("destination_depot_id")
    route_depots_raw = request.form.get("route_depots", "[]") # List of depot codes along path
    item_name = request.form.get("item_name")
    item_description = request.form.get("item_description")
    date_lost = request.form.get("date_lost") # Expected format: YYYY-MM-DD
    contact_phone = request.form.get("contact_phone")
    bus_number = request.form.get("bus_number", "") # Optional

    # Requirement Check: Bus number is optional, but description and contact are mandatory
    if not all([source_depot_id, destination_depot_id, item_name, item_description, date_lost, contact_phone]):
        return jsonify({"message": "Critical information missing"}), 400

    try:
        route_depots = json.loads(route_depots_raw)
    except Exception:
        route_depots = []

    # Handle Photo Upload (Optional for lost, mandatory for found)
    photo_url = None
    if 'photo' in request.files:
        photo = request.files['photo']
        if photo and allowed_file(photo.filename):
            filename = secure_filename(f"lost_{uuid.uuid4().hex}_{photo.filename}")
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            photo.save(filepath)
            photo_url = f"/uploads/{filename}"

    report = {
        "user_id": request.user["id"],
        "source_depot_id": source_depot_id,
        "destination_depot_id": destination_depot_id,
        "route_depots": route_depots,
        "item_name": item_name.strip(),
        "item_description": item_description.strip(),
        "date_lost": date_lost,
        "bus_number": bus_number.strip(),
        "contact_phone": contact_phone.strip(),
        "photo_url": photo_url,
        "status": "reported",
        "created_at": datetime.now(timezone.utc),
    }

    result = mongo.db.lost_luggage_reports.insert_one(report)
    report["_id"] = result.inserted_id

    # ENHANCED MATCHING LOGIC
    search_depots = route_depots if route_depots else [source_depot_id, destination_depot_id]
    
    # Requirement: Match items found ON or BEFORE the reported loss date (if travel allows)
    # Actually, logic should be: if I lost it today, matching found items should be since that date?
    # No, typically if I lost it today, I want to see if someone found it today. 
    # If someone found it yesterday, it's NOT my item.
    # So: found_date >= date_lost.
    
    found_cursor = mongo.db.found_luggage.find({
        "depot_id": {"$in": search_depots},
        "found_date": {"$gte": date_lost}
    })
    found_items = list(found_cursor)

    matches = []
    if found_items:
        processed_found = []
        for f in found_items:
            processed_found.append({
                "found_id": str(f["_id"]),
                "description": f.get("description", ""),
                "photo_url": f.get("photo_url"),
                "depot_id": f.get("depot_id"),
                "found_date": f.get("found_date")
            })
        
        matches = matcher.find_matches(item_description, processed_found, threshold=0.35)

    # Real-time notification to managers along the route
    for d_id in search_depots:
        socketio.emit("new_lost_report", {"report": _report_to_dict(report)}, room=f"depot_{d_id}")

    return jsonify({
        "message": "Report submitted",
        "report": _report_to_dict(report),
        "matches": matches[:10] 
    }), 201

@luggage_bp.get("/my-reports")
@jwt_required()
def my_reports():
    """Return all reports created by the current user."""
    cursor = mongo.db.lost_luggage_reports.find({"user_id": request.user["id"]}).sort(
        "created_at", -1
    )
    return jsonify({"reports": [_report_to_dict(r) for r in cursor]})

@luggage_bp.get("/matches/<report_id>")
@jwt_required()
def get_my_report_matches(report_id):
    """Securely return date-filtered and route-aware AI matches for the user's report."""
    try:
        report = mongo.db.lost_luggage_reports.find_one({
            "_id": ObjectId(report_id),
            "user_id": request.user["id"]
        })
    except Exception:
        return jsonify({"message": "Invalid report ID"}), 400

    if not report:
        return jsonify({"message": "Report not found"}), 404

    # Matching logic: Search found_luggage in depots along the route
    search_depots = report.get("route_depots", [])
    if not search_depots:
        search_depots = [report["source_depot_id"], report["destination_depot_id"]]

    # Requirement: Match items found ON OR AFTER the loss date
    # items found before the loss date are logically impossible to be this item.
    found_cursor = mongo.db.found_luggage.find({
        "depot_id": {"$in": search_depots},
        "found_date": {"$gte": report.get("date_lost", "0000-00-00")}
    })
    
    found_items = []
    for f in found_cursor:
        found_items.append({
            "id": str(f["_id"]),
            "description": f.get("description", ""),
            "photo_url": f.get("photo_url"),
            "depot_id": f.get("depot_id"),
            "found_date": f.get("found_date")
        })

    if not found_items:
        return jsonify({"matches": []})

    # AI Match Score Calculation
    matches = matcher.find_matches(report.get("item_description", ""), found_items, threshold=0.35)
    return jsonify({"matches": matches})
