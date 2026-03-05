from datetime import datetime, timezone

from bson import ObjectId
from flask import Blueprint, jsonify, request

from ..extensions import bcrypt, mongo
from .jwt_handler import create_access_token, jwt_required
from .oauth import (
    exchange_google_code_for_userinfo,
    exchange_ms_code_for_userinfo,
    get_google_auth_url,
    get_ms_auth_url,
)

auth_bp = Blueprint("auth", __name__)


def _user_to_safe_dict(user: dict) -> dict:
    """Helper to remove sensitive info including password hashes."""
    from ..extensions import mongo
    
    data = {
        "id": str(user["_id"]),
        "name": user.get("name"),
        "email": user.get("email"),
        "role": user.get("role", "user"),
        "assigned_depot_id": user.get("assigned_depot_id"),
    }
    
    # If manager, join with depots to get the name
    if data["role"] == "manager" and data["assigned_depot_id"]:
        depot = mongo.db.depots.find_one({"depot_id": data["assigned_depot_id"]})
        if depot:
            data["assigned_depot_name"] = depot.get("name")
            
    return data


@auth_bp.post("/signup")
def signup():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    # Security: Public signup is strictly for passengers. 
    # Official/Manager accounts are created via backend scripts only.
    role = "user" 

    if not all([name, email, password]):
        return jsonify({"message": "Name, email and password are required"}), 400

    try:
        users = mongo.db.users
        if users.find_one({"email": email}):
            return jsonify({"message": "Email already registered"}), 400

        pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        user = {
            "name": name,
            "email": email,
            "password_hash": pw_hash,
            "google_id": None,
            "microsoft_id": None,
            "role": role,
            "assigned_depot_id": None, # For managers, this needs manual assignment later or during signup
            "created_at": datetime.now(timezone.utc),
        }
        result = users.insert_one(user)
        user["_id"] = result.inserted_id

    except Exception as e:
        print(f"❌ Database error during signup: {e}")
        return jsonify({"message": "Database error. Please check if MongoDB is reachable."}), 500

    token = create_access_token(str(user["_id"]), user["role"])
    return jsonify({"token": token, "user": _user_to_safe_dict(user)}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not all([email, password]):
        return jsonify({"message": "Email and password are required"}), 400

    users = mongo.db.users
    user = users.find_one({"email": email})
    if not user or not user.get("password_hash"):
        return jsonify({"message": "Invalid credentials"}), 401

    if not bcrypt.check_password_hash(user["password_hash"], password):
        return jsonify({"message": "Invalid credentials"}), 401

    token = create_access_token(str(user["_id"]), user.get("role", "user"))
    return jsonify({"token": token, "user": _user_to_safe_dict(user)}), 200


@auth_bp.get("/google/url")
def google_auth_url():
    """Return the Google OAuth URL so frontend can redirect user."""
    state = "secure-random-state"  # In production, generate and store per-session
    url = get_google_auth_url(state)
    return jsonify({"url": url})


@auth_bp.get("/google/callback")
def google_callback():
    code = request.args.get("code")
    if not code:
        return jsonify({"message": "Missing authorization code"}), 400

    profile = exchange_google_code_for_userinfo(code)
    if not profile:
        return jsonify({"message": "Failed to fetch Google profile"}), 400

    google_id = profile.get("sub")
    email = (profile.get("email") or "").lower()
    name = profile.get("name") or email

    users = mongo.db.users
    user = users.find_one({"google_id": google_id}) or users.find_one({"email": email})

    if not user:
        user = {
            "name": name,
            "email": email,
            "password_hash": None,
            "google_id": google_id,
            "microsoft_id": None,
            "role": "user",
            "assigned_depot_id": None,
            "created_at": datetime.now(timezone.utc),
        }
        result = users.insert_one(user)
        user["_id"] = result.inserted_id
    else:
        users.update_one(
            {"_id": user["_id"]},
            {"$set": {"google_id": google_id, "name": name}},
        )

    token = create_access_token(str(user["_id"]), user.get("role", "user"))
    # In a SPA we would redirect with token as fragment; here we just return JSON.
    return jsonify({"token": token, "user": _user_to_safe_dict(user)})


@auth_bp.get("/microsoft/url")
def microsoft_auth_url():
    state = "secure-random-state"
    url = get_ms_auth_url(state)
    return jsonify({"url": url})


@auth_bp.get("/microsoft/callback")
def microsoft_callback():
    code = request.args.get("code")
    if not code:
        return jsonify({"message": "Missing authorization code"}), 400

    profile = exchange_ms_code_for_userinfo(code)
    if not profile:
        return jsonify({"message": "Failed to fetch Microsoft profile"}), 400

    ms_id = profile.get("id")
    email = (profile.get("mail") or profile.get("userPrincipalName") or "").lower()
    name = profile.get("displayName") or email

    users = mongo.db.users
    user = users.find_one({"microsoft_id": ms_id}) or users.find_one({"email": email})

    if not user:
        user = {
            "name": name,
            "email": email,
            "password_hash": None,
            "google_id": None,
            "microsoft_id": ms_id,
            "role": "user",
            "assigned_depot_id": None,
            "created_at": datetime.now(timezone.utc),
        }
        result = users.insert_one(user)
        user["_id"] = result.inserted_id
    else:
        users.update_one(
            {"_id": user["_id"]},
            {"$set": {"microsoft_id": ms_id, "name": name}},
        )

    token = create_access_token(str(user["_id"]), user.get("role", "user"))
    return jsonify({"token": token, "user": _user_to_safe_dict(user)})


@auth_bp.get("/me")
@jwt_required()
def me():
    users = mongo.db.users
    try:
        user = users.find_one({"_id": ObjectId(request.user["id"])})
    except Exception:
        return jsonify({"message": "User not found"}), 404

    if not user:
        return jsonify({"message": "User not found"}), 404
    return jsonify({"user": _user_to_safe_dict(user)})


