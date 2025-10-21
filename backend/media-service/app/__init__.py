import os
from flask import Flask
from .config import Config
from .extensions import cors
from .utils.ffmpeg import check_ffmpeg
from .controllers.upload_controller import upload_bp
from .controllers.admin_controller import admin_bp
from .controllers.files_controller import files_bp
from .controllers.health_controller import health_bp

def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config())

    cors.init_app(app, resources={r"/*": {"origins": os.getenv("CORS_ORIGINS", "*")}})
    check_ffmpeg()

    app.register_blueprint(health_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    return app
