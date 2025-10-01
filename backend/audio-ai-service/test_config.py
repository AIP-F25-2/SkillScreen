from config import settings, logger

logger.info("Testing configuration")
logger.info(f"App Name: {settings.APP_NAME}")
logger.info(f"Environment: {settings.ENVIRONMENT}")
logger.info(f"Whisper Model: {settings.WHISPER_MODEL_SIZE}")
logger.info(f"Temp Dir: {settings.TEMP_AUDIO_DIR}")

print("\nConfiguration loaded successfully!")
print(f"Directories created: {settings.TEMP_AUDIO_DIR}, {settings.MODEL_CACHE_DIR}")