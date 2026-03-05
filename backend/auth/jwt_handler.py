import functools
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import jwt
from flask import current_app, jsonify, request


def create_access_token(user_id: str, role: str) -> str:
    """Create a signed JWT access token."""
    now = datetime.now(timezone.utc)
    expires = now + current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]

    payload = {
        "sub": user_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
    }
    token = jwt.encode(
        payload,
        current_app.config["JWT_SECRET_KEY"],
        algorithm=current_app.config["JWT_ALGORITHM"],
    )
    # PyJWT >= 2 returns str, but older returns bytes
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        data = jwt.decode(
            token,
            current_app.config["JWT_SECRET_KEY"],
            algorithms=[current_app.config["JWT_ALGORITHM"]],
        )
        return data
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def _get_token_from_header() -> Optional[str]:
    auth_header = request.headers.get("Authorization", "")
    parts = auth_header.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


def jwt_required(roles: Optional[list[str]] = None):
    """
    Decorator to protect routes with JWT.

    Usage:
        @jwt_required()
        def my_route(): ...

        @jwt_required(roles=["manager"])
        def manager_only(): ...
    """

    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            token = _get_token_from_header()
            if not token:
                return jsonify({"message": "Missing Authorization header"}), 401

            payload = decode_token(token)
            if not payload:
                return jsonify({"message": "Invalid or expired token"}), 401

            if roles and payload.get("role") not in roles:
                return jsonify({"message": "Insufficient permissions"}), 403

            # Attach user info to request context
            request.user = {
                "id": payload.get("sub"),
                "role": payload.get("role"),
            }
            return fn(*args, **kwargs)

        return wrapper

    return decorator

