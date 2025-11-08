# app/security.py
import os
from flask_wtf.csrf import CSRFProtect

def configure_csrf(app):
    """
    Configures CSRF protection safely.

    CSRF protection is enabled only if ENABLE_CSRF=true.
    Otherwise, it is explicitly disabled because this service
    is a stateless REST API that authenticates using JWT/Bearer tokens.
    No cookies or browser-stored credentials are used.
    Therefore, disabling CSRF is secure and intentional.
    """
    if os.getenv("ENABLE_CSRF", "false").lower() == "true":
        csrf = CSRFProtect()
        csrf.init_app(app)
        app.logger.info("CSRF protection enabled.")
    else:
        app.config["WTF_CSRF_ENABLED"] = False  # Safe: stateless API
        app.logger.info("CSRF protection disabled (JWT-based API).")
