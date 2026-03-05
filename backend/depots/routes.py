from datetime import datetime, timezone

from bson import ObjectId
from flask import Blueprint, jsonify, request

from ..auth.jwt_handler import jwt_required
from ..extensions import mongo

depots_bp = Blueprint("depots", __name__)


def _depot_to_dict(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "depot_id": doc.get("depot_id", ""),
        "name": doc.get("name"),
        "city": doc.get("city"),
        "district": doc.get("district"),
        "type": doc.get("type", "TNSTC"),
        "latitude": doc.get("latitude"),
        "longitude": doc.get("longitude"),
        "contact_number": doc.get("contact_number", ""),
    }


@depots_bp.get("/depots")
def list_depots():
    """Return all depots for Leaflet map markers."""
    depots = mongo.db.depots.find()
    return jsonify({"depots": [_depot_to_dict(d) for d in depots]})


@depots_bp.get("/depots/search")
def search_depots():
    """Fuzzy search depots by name, city, or district."""
    query = (request.args.get("q") or "").strip().lower()
    if not query:
        depots = list(mongo.db.depots.find().limit(10))
        return jsonify({"depots": [_depot_to_dict(d) for d in depots]})

    try:
        from thefuzz import fuzz
        all_depots = list(mongo.db.depots.find())
        scored = []
        for d in all_depots:
            search_text = f"{d.get('name', '')} {d.get('city', '')} {d.get('district', '')} {d.get('type', '')}".lower()
            score = max(
                fuzz.partial_ratio(query, search_text),
                fuzz.token_set_ratio(query, search_text),
            )
            if score >= 45:
                scored.append((score, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = [_depot_to_dict(d) for _, d in scored[:10]]
    except ImportError:
        # Fallback: simple substring match
        query_lower = query.lower()
        all_depots = list(mongo.db.depots.find())
        results = [
            _depot_to_dict(d) for d in all_depots
            if query_lower in (d.get("name", "") + " " + d.get("city", "") + " " + d.get("district", "")).lower()
        ][:10]

    return jsonify({"depots": results, "query": query})


@depots_bp.post("/depot/select")
@jwt_required()
def select_depot_spec():
    """
    Spec-required endpoint: POST /api/depot/select
    Accepts: { depotId, depotName, lat, lng }
    """
    data = request.get_json() or {}
    depot_id_code = data.get("depotId") or data.get("depot_id")
    depot_name = data.get("depotName") or data.get("name") or ""
    lat = data.get("lat")
    lng = data.get("lng")

    if not depot_id_code:
        return jsonify({"message": "depotId is required"}), 400

    # Try lookup by string depot_id first, then by ObjectId
    depot = mongo.db.depots.find_one({"depot_id": depot_id_code})
    if not depot:
        try:
            depot = mongo.db.depots.find_one({"_id": ObjectId(depot_id_code)})
        except Exception:
            pass

    if not depot:
        return jsonify({"message": "Depot not found"}), 404

    selected = {
        "user_id": request.user["id"],
        "depot_id": str(depot["_id"]),
        "depot_code": depot.get("depot_id", ""),
        "depot_name": depot_name or depot.get("name"),
        "lat": lat or depot.get("latitude"),
        "lng": lng or depot.get("longitude"),
        "selected_at": datetime.now(timezone.utc),
    }
    mongo.db.selected_depots.insert_one(selected)
    return jsonify({"message": "Depot selected", "depot": _depot_to_dict(depot)}), 201


@depots_bp.post("/select-depot")
@jwt_required()
def select_depot_legacy():
    """Legacy endpoint kept for backward compatibility."""
    data = request.get_json() or {}
    depot_id = data.get("depot_id")
    if not depot_id:
        return jsonify({"message": "depot_id is required"}), 400

    try:
        depot_obj_id = ObjectId(depot_id)
    except Exception:
        return jsonify({"message": "Invalid depot_id"}), 400

    depot = mongo.db.depots.find_one({"_id": depot_obj_id})
    if not depot:
        return jsonify({"message": "Depot not found"}), 404

    selected = {
        "user_id": request.user["id"],
        "depot_id": depot_id,
        "depot_code": depot.get("depot_id", ""),
        "selected_at": datetime.now(timezone.utc),
    }
    mongo.db.selected_depots.insert_one(selected)
    return jsonify({"message": "Depot selected", "depot": _depot_to_dict(depot)}), 201
