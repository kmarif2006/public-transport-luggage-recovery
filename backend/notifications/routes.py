from datetime import datetime, timezone
from bson import ObjectId
from flask import Blueprint, jsonify, request

from ..auth.jwt_handler import jwt_required
from ..extensions import mongo

notifications_bp = Blueprint("notifications", __name__)


def _notif_to_dict(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "user_id": doc.get("user_id"),
        "report_id": doc.get("report_id"),
        "found_id": doc.get("found_id"),
        "item_name": doc.get("item_name"),
        "item_description": doc.get("item_description"),
        "match_score": doc.get("match_score"),
        "found_description": doc.get("found_description"),
        "found_photo_url": doc.get("found_photo_url"),
        "depot_id": doc.get("depot_id"),
        "found_date": doc.get("found_date"),
        "read": doc.get("read", False),
        "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else None,
    }


@notifications_bp.get("/notifications")
@jwt_required()
def get_notifications():
    """Return all notifications for the logged-in user."""
    user_id = request.user["id"]
    cursor = mongo.db.notifications.find({"user_id": user_id}).sort("created_at", -1).limit(50)
    notifications = [_notif_to_dict(n) for n in cursor]
    unread_count = sum(1 for n in notifications if not n["read"])
    return jsonify({"notifications": notifications, "unread_count": unread_count})


@notifications_bp.put("/notifications/<notif_id>/read")
@jwt_required()
def mark_notification_read(notif_id):
    """Mark a specific notification as read."""
    user_id = request.user["id"]
    try:
        result = mongo.db.notifications.update_one(
            {"_id": ObjectId(notif_id), "user_id": user_id},
            {"$set": {"read": True, "read_at": datetime.now(timezone.utc)}}
        )
        if result.matched_count == 0:
            return jsonify({"message": "Notification not found"}), 404
        return jsonify({"message": "Marked as read"})
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500


@notifications_bp.put("/notifications/read-all")
@jwt_required()
def mark_all_read():
    """Mark all notifications for the logged-in user as read."""
    user_id = request.user["id"]
    mongo.db.notifications.update_many(
        {"user_id": user_id, "read": False},
        {"$set": {"read": True, "read_at": datetime.now(timezone.utc)}}
    )
    return jsonify({"message": "All notifications marked as read"})
