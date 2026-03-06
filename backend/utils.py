"""
backend/utils.py — Shared helper functions across blueprints.
Prevents circular imports by keeping serialization logic in one place.
"""


def report_to_dict(doc: dict) -> dict:
    """Serialize a lost_luggage_reports MongoDB document to a safe dict."""
    return {
        "id"                   : str(doc["_id"]),
        "user_id"              : doc.get("user_id"),
        "source_depot_id"      : doc.get("source_depot_id"),
        "destination_depot_id" : doc.get("destination_depot_id"),
        "route_depots"         : doc.get("route_depots", []),
        "item_name"            : doc.get("item_name"),
        "item_description"     : doc.get("item_description"),
        "date_lost"            : doc.get("date_lost"),
        "bus_number"           : doc.get("bus_number"),
        "contact_phone"        : doc.get("contact_phone"),
        "photo_url"            : doc.get("photo_url"),
        "status"               : doc.get("status", "reported"),
        "created_at"           : doc.get("created_at").isoformat() if doc.get("created_at") else None,
        "updated_at"           : doc.get("updated_at").isoformat() if doc.get("updated_at") else None,
    }


def found_item_to_dict(doc: dict) -> dict:
    """Serialize a found_luggage MongoDB document to a safe dict."""
    return {
        "id"         : str(doc["_id"]),
        "depot_id"   : doc.get("depot_id"),
        "description": doc.get("description"),
        "found_date" : doc.get("found_date"),
        "photo_url"  : doc.get("photo_url"),
        "created_at" : doc.get("created_at").isoformat() if doc.get("created_at") else None,
    }
