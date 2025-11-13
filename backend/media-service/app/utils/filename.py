import os
from werkzeug.utils import secure_filename as _secure
def secure_part(value: str) -> str:
    return _secure(os.path.basename(value or ""))
def allowed_ext(filename: str, allowed: set | None) -> bool:
    if allowed is None:
        return True
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed
