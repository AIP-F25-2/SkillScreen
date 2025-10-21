import os
from flask import current_app
from ..utils.filename import secure_part

def create_user(user_id: str) -> bool:
    base = current_app.config["UPLOAD_FOLDER"]
    uid = secure_part(user_id)
    folder = os.path.join(base, uid)
    if os.path.exists(folder):
        return False
    os.makedirs(folder, exist_ok=True)
    return True
