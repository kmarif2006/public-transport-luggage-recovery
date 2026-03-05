import os
from datetime import timedelta


class Config:
    """Base configuration shared across environments."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "tn-bus-lost-found-dev-key-2026")
    DEBUG = False

    # MongoDB Atlas connection
    MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/tn_bus_lost_luggage")
    MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME", "tn_bus_lost_luggage")

    # JWT configuration
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=4)

    # CORS
    CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "*")

    # OAuth - Google
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
    GOOGLE_OAUTH_REDIRECT_URI = os.environ.get(
        "GOOGLE_OAUTH_REDIRECT_URI",
        "http://localhost:5000/api/auth/google/callback",
    )

    # OAuth - Microsoft
    MS_CLIENT_ID = os.environ.get("MS_CLIENT_ID")
    MS_CLIENT_SECRET = os.environ.get("MS_CLIENT_SECRET")
    MS_OAUTH_REDIRECT_URI = os.environ.get(
        "MS_OAUTH_REDIRECT_URI",
        "http://localhost:5000/api/auth/microsoft/callback",
    )


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False

