import os
import uuid
from datetime import datetime, timezone
from bson import ObjectId
from flask import Blueprint, jsonify, request, current_app
from werkzeug.utils import secure_filename

from ..auth.jwt_handler import jwt_required
from ..extensions import mongo, socketio
from ..luggage.routes import _report_to_dict
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
    
    # Logic: Reports are relevant if the bus passed through this depot (Source, Dest, or Route)
    cursor = mongo.db.lost_luggage_reports.find({
        "$or": [
            {"source_depot_id": depot_id},
            {"destination_depot_id": depot_id},
            {"route_depots": depot_id}
        ]
    }).sort("created_at", -1)
    
    return jsonify({"reports": [_report_to_dict(r) for r in cursor]})

@manager_bp.post("/found-luggage")
@jwt_required(roles=["manager"])
def post_found_luggage():
    """Manager registers found luggage. Description and Photo are strictly mandatory for accountability."""
    description = request.form.get("description")
    found_date = request.form.get("found_date") # YYYY-MM-DD
    
    if not all([description, found_date]):
        return jsonify({"message": "Missing mandatory found item details"}), 400
        
    if 'photo' not in request.files:
        return jsonify({"message": "Photo evidence is mandatory for found luggage registration"}), 400

    manager = mongo.db.users.find_one({"_id": ObjectId(request.user["id"])})
    depot_id = manager.get("assigned_depot_id")
    
    photo = request.files['photo']
    if not photo or not allowed_file(photo.filename):
        return jsonify({"message": "Invalid file format for photo evidence"}), 400
        
    # Secure filename for government portal standards
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
    
    # Matching check: Logically we could trigger an alert to passengers here
    # but the passive matching happens on the passenger dashboard.
    
    return jsonify({
        "message": "Found luggage successfully registered in depot ledger",
        "id": str(result.inserted_id),
        "photo_url": photo_url
    }), 201

@manager_bp.put("/update-status")
@jwt_required(roles=["manager"])
def update_report_status():
    """Authorized update of lost luggage status (Reported -> Under Review -> Found -> Returned)."""
    data = request.get_json() or {}
    report_id = data.get("report_id")
    new_status = data.get("status")

    if not all([report_id, new_status]):
        return jsonify({"message": "report_id and status are required for trace updates"}), 400

    manager = mongo.db.users.find_one({"_id": ObjectId(request.user["id"])})
    depot_id = manager.get("assigned_depot_id")

    try:
        # Verification: Only managers of depots on the route can update status
        report = mongo.db.lost_luggage_reports.find_one({"_id": ObjectId(report_id)})
        if not report:
            return jsonify({"message": "Report record not found"}), 404
            
        is_authorized = (
            report.get("source_depot_id") == depot_id or
            report.get("destination_depot_id") == depot_id or
            depot_id in report.get("route_depots", [])
        )
        
        if not is_authorized:
            return jsonify({"message": "Unauthorized: This report is not passing through your assigned depot"}), 403

        mongo.db.lost_luggage_reports.update_one(
            {"_id": ObjectId(report_id)},
            {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc)}}
        )
            
        return jsonify({"message": f"Status updated to: {new_status}", "status": new_status}), 200
    except Exception as e:
        print(f"[ERROR] Status update failed: {e}")
        return jsonify({"message": "Server error during status update"}), 500
