from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_socketio import SocketIO, join_room
from pymongo import MongoClient

bcrypt = Bcrypt()
cors = CORS()
socketio = SocketIO(cors_allowed_origins="*")


class Mongo:
    """Simple MongoDB helper to access the configured database."""

    def __init__(self):
        self.client = None
        self.db = None

    def init_app(self, app):
        uri = app.config.get("MONGODB_URI")
        db_name = app.config.get("MONGODB_DB_NAME")
        try:
            # Added tls=True and tlsAllowInvalidCertificates for better compatibility on Windows
            self.client = MongoClient(
                uri, 
                serverSelectionTimeoutMS=5000, 
                tls=True,
                tlsAllowInvalidCertificates=True
            )
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[db_name]
            print(f"--- MongoDB connected to '{db_name}'")
        except Exception as e:
            print(f"!!! MongoDB connection error: {e}")
            # Initialize anyway so the app doesn't crash on startup
            self.client = MongoClient(
                uri, 
                serverSelectionTimeoutMS=2000, 
                tls=True,
                tlsAllowInvalidCertificates=True
            )
            self.db = self.client[db_name]


mongo = Mongo()


def init_extensions(app):
    """Initialize all Flask extensions with the application factory."""
    bcrypt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config.get("CORS_ALLOWED_ORIGINS", "*")}})
    mongo.init_app(app)
    socketio.init_app(app)

