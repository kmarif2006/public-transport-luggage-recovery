import os

from dotenv import load_dotenv

# Load .env once at startup for local/dev environments
load_dotenv()

from flask import Flask, redirect, request, url_for
from flask_socketio import join_room

from .config import DevelopmentConfig, ProductionConfig
from .extensions import init_extensions, socketio
from .auth.jwt_handler import decode_token
from .auth.routes import auth_bp
from .depots.routes import depots_bp
from .luggage.routes import luggage_bp
from .manager.routes import manager_bp


def create_app() -> Flask:
    """Application factory for the TN Bus Lost Luggage system."""

    env = os.environ.get("FLASK_ENV", "development")
    config_cls = DevelopmentConfig if env != "production" else ProductionConfig

    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "frontend"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "frontend"),
        static_url_path="/",
    )
    app.config.from_object(config_cls)

    # Upload configuration
    upload_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'static', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB limit

    # Extensions
    from .extensions import bcrypt, cors, mongo, socketio
    bcrypt.init_app(app)
    cors.init_app(app)
    mongo.init_app(app)
    socketio.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(depots_bp, url_prefix="/api")
    app.register_blueprint(luggage_bp, url_prefix="/api")
    app.register_blueprint(manager_bp, url_prefix="/api/manager")

    # Serve uploads from static
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        from flask import send_from_directory
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # Serve frontend pages
    @app.get("/")
    def root():
        return redirect(url_for("static", filename="login.html"))

    @app.get("/login")
    def login_page():
        return app.send_static_file("login.html")

    @app.get("/login.html")
    def login_page_direct():
        return app.send_static_file("login.html")

    @app.get("/signup")
    def signup_page():
        return app.send_static_file("signup.html")

    @app.get("/signup.html")
    def signup_page_direct():
        return app.send_static_file("signup.html")

    @app.get("/map")
    def map_page():
        return app.send_static_file("map.html")

    @app.get("/map.html")
    def map_page_direct():
        return app.send_static_file("map.html")

    @app.get("/dashboard")
    def dashboard_page():
        return app.send_static_file("dashboard.html")

    @app.get("/dashboard.html")
    def dashboard_page_direct():
        return app.send_static_file("dashboard.html")

    @app.get("/manager_dashboard")
    def manager_dashboard_page():
        return app.send_static_file("manager_dashboard.html")

    @app.get("/manager_dashboard.html")
    def manager_dashboard_page_direct():
        return app.send_static_file("manager_dashboard.html")

    @app.get("/depot_login")
    def depot_login_page():
        return app.send_static_file("depot_login.html")

    @app.get("/depot_login.html")
    def depot_login_page_direct():
        return app.send_static_file("depot_login.html")

    @socketio.on("connect")
    def socket_connect(auth):
        """
        Authenticate Socket.IO connections using the same JWT and join depot room for managers.
        """
        from flask import session

        token = None
        if isinstance(auth, dict):
            token = auth.get("token")
        if not token:
            return False  # reject

        payload = decode_token(token)
        if not payload:
            return False

        # Only managers need room-based notifications
        if payload.get("role") == "manager":
            from bson import ObjectId

            # Lazy import to avoid circulars
            from .extensions import mongo

            try:
                manager = mongo.db.users.find_one({"_id": ObjectId(payload["sub"])})
                depot_id = manager.get("assigned_depot_id") if manager else None
                if depot_id:
                    join_room(f"depot_{depot_id}")
            except Exception:
                pass  # Handle MongoDB connection errors gracefully

    return app

