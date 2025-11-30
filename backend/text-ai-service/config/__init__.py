from .settings import Settings, settings
from .logging_config import setup_logging

logger = setup_logging(settings.LOG_LEVEL)

__all__ = ["settings", "logger", "setup_logging"]
