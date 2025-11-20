from datetime import datetime
import uuid

def create_response(data, success: bool = True):
    return {
        "success": success,
        "data": data,
        "meta": {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": f"req_{uuid.uuid4().hex[:8]}",
            "version": "v1"
        }
    }