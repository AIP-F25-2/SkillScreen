from flask import Blueprint, render_template, jsonify
health_bp = Blueprint("health", __name__)
from ..repositories.media_repository import MediaRepository
from db import UnitOfWork
import json

uow = UnitOfWork()
repos= MediaRepository(uow)

@health_bp.route("/")
def index():
    return render_template("index.html")

@health_bp.route("/healthz")
def healthz():
    # results = repos.get_all_media_files()
    # return jsonify({"status": "ok","results":dict(results)}), 200
    return jsonify({"status": "ok"}), 200
