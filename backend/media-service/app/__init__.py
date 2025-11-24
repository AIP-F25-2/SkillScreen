# app.__init__.py

import os
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from .config import Config
from .extensions import cors
from .utils.ffmpeg import check_ffmpeg
from .controllers.upload_controller import upload_bp
from .controllers.admin_controller import admin_bp
from .controllers.files_controller import files_bp
from .controllers.health_controller import health_bp
from .controllers.interview_controller import interview_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config())

    if os.getenv("ENABLE_CSRF", "false").lower() == "true":
        csrf = CSRFProtect()
        csrf.init_app(app)
        app.logger.info("CSRF protection enabled.")

    # ---- CORS ----
    cors.init_app(
        app,
        resources={r"/*": {"origins": os.getenv("CORS_ORIGINS", "https://your-frontend.com")}},
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
        supports_credentials=False,  # No cookies — CSRF not applicable
    )

    # ---- System check ----
    check_ffmpeg()

    # ---- Register Blueprints ----
    app.register_blueprint(health_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(interview_bp)

    return app