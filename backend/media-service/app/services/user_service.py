# app/services/user_service.py
from flask import current_app
from ..utils.filename import secure_part
from .storage_service import StorageService

def create_user(user_id: str) -> bool:
    # No actual folder creation needed for Azure; return False if already exists (optional)
    uid = secure_part(user_id)
    existing = StorageService.list_users()
    if uid in existing:
        return False
    # lazy model: nothing to create; first upload will implicitly create the prefix
    return True
