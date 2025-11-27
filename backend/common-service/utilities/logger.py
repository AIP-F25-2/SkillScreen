import logging
import os
from logging.handlers import RotatingFileHandler

try:
    from pythonjsonlogger import jsonlogger
except Exception:
    jsonlogger = None

try:
    import seqlog
except Exception:
    seqlog = None

_INITIALIZED = False
_SEQ_ENABLED = False


def init_logger(service_name: str) -> logging.Logger:
    """
    Initializes the logger once for each service.
    Supports:
      - Rotating file logs
      - Optional Seq sink (via ENABLE_SEQ & SEQ_URL)
    """
    global _INITIALIZED, _SEQ_ENABLED

    if _INITIALIZED:
        return logging.getLogger(service_name)

    # ----- Set log level -----
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    # ----- Root setup -----
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.handlers.clear()

    # ----- File handler -----
    if os.getenv("LOG_TO_FILE", "true").lower() == "true":
        log_dir = os.getenv("LOG_DIR", "/var/log/app")
        log_file = os.getenv("LOG_FILE", f"{service_name}.log")
        max_bytes = int(os.getenv("LOG_MAX_BYTES", str(5 * 1024 * 1024)))  # 5MB
        backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))

        os.makedirs(log_dir, exist_ok=True)
        file_path = os.path.join(log_dir, log_file)

        fh = RotatingFileHandler(
            filename=file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )

        if jsonlogger:
            formatter = jsonlogger.JsonFormatter(
                fmt="%(asctime)s %(levelname)s %(name)s %(message)s %(module)s %(funcName)s %(lineno)d",
                rename_fields={"levelname": "level", "name": "logger"},
            )
        else:
            formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")

        fh.setFormatter(formatter)
        fh.setLevel(level)
        root.addHandler(fh)

    # ----- Seq logging -----
    _SEQ_ENABLED = os.getenv("ENABLE_SEQ", "false").lower() == "true"
    seq_url = os.getenv("SEQ_URL")

    if _SEQ_ENABLED:
        if not seqlog:
            logging.getLogger(__name__).warning(
                "ENABLE_SEQ=true but 'seqlog' is not installed. Run: pip install seqlog"
            )
            _SEQ_ENABLED = False
        elif not seq_url:
            logging.getLogger(__name__).warning(
                "ENABLE_SEQ=true but SEQ_URL is not set. Disabling Seq sink."
            )
            _SEQ_ENABLED = False
        else:
            try:
                seq_min = getattr(logging, os.getenv("SEQ_MIN_LEVEL", level_name).upper(), level)
                # Try to configure Seq logging with retry logic
                # Note: default_properties is not supported in seqlog 0.3.31
                # Service name will be included via logger name
                seqlog.log_to_seq(
                    server_url=seq_url,
                    level=seq_min,
                    batch_size=10,
                    auto_flush_timeout=2.0,
                    override_root_logger=True  # send everything including root logs
                )
                # Set up structured logging with service context via logger name
                service_logger = logging.getLogger(service_name)
                service_logger.setLevel(level)
                logging.getLogger(__name__).info(
                    f"Seq logging enabled at {seq_url} for {service_name}"
                )
            except (ConnectionError, OSError) as e:
                # Connection errors - Seq might not be ready yet, but service should continue
                # These errors are expected during startup if Seq is still initializing
                logging.getLogger(__name__).warning(
                    f"Seq connection failed (service will continue, Seq may not be ready yet): {e}"
                )
                _SEQ_ENABLED = False
            except Exception as e:
                # Other errors - log but don't fail
                logging.getLogger(__name__).warning(
                    f"Failed to configure Seq logging (service will continue): {e}"
                )
                _SEQ_ENABLED = False

    _INITIALIZED = True

    logger = logging.getLogger(service_name)
    logger.setLevel(level)
    logger.info(
        "logger_initialized",
        extra={
            "service": service_name,
            "file_logging": os.getenv("LOG_TO_FILE", "true").lower() == "true",
            "seq_enabled": _SEQ_ENABLED,
        },
    )
    return logger


def get_logger(service_name: str) -> logging.Logger:
    return logging.getLogger(service_name)
