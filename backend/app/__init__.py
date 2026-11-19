import os

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from app.config import Config

db = SQLAlchemy()
jwt = JWTManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    db.init_app(app)
    jwt.init_app(app)

    # These imports must stay INSIDE the function (after db exists)
    from app.routes.chat_routes import chat_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.dashboard_routes import dashboard_bp
    from app.routes.analytics_routes import analytics_bp

    app.register_blueprint(chat_bp, url_prefix="/api/chat")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")

    # Production mode: if the React app has been built (npm run build in frontend/),
    # Flask serves it too, so the whole project runs from one command.
    dist = os.path.abspath(os.path.join(app.root_path, "..", "..", "frontend", "dist"))
    if os.path.isdir(dist):
        @app.route("/", defaults={"path": ""})
        @app.route("/<path:path>")
        def serve_frontend(path):
            if path.startswith("api/"):
                return jsonify({"error": "Not found"}), 404
            if path and os.path.isfile(os.path.join(dist, path)):
                return send_from_directory(dist, path)
            return send_from_directory(dist, "index.html")

    with app.app_context():
        from app import models  # noqa: F401  (registers every model before create_all)
        db.create_all()

    return app