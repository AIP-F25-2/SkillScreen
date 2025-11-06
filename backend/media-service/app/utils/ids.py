# app/utils/ids.py
import uuid
from typing import Optional, Union

def normalize_uuid(val: Optional[str]) -> Optional[uuid.UUID]:
    """
    Return a uuid.UUID for any input string.
    - If already a valid UUID -> keep it.
    - If not, derive a deterministic UUIDv5 from the input.
    - If None/empty -> None.
    """
    if not val:
        return None
    try:
        return uuid.UUID(val)
    except Exception:
        # Deterministic mapping so the same session string filters correctly later
        return uuid.uuid5(uuid.NAMESPACE_URL, val)
