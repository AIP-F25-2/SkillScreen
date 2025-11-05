#!/usr/bin/env python3
"""
Run Polling Service - Entry point for audio-ai-service polling
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from config import logger, settings
from services.polling_service import PollingService


def main():
    """
    Main entry point for polling service
    """
    logger.info("=" * 60)
    logger.info("🎯 SkillScreen Audio AI Service - Polling Mode")
    logger.info("=" * 60)
    
    # Check if polling is enabled
    if not getattr(settings, 'POLLING_ENABLED', True):
        logger.warning("⚠️ Polling is disabled in settings. Exiting.")
        return
    
    # Get configuration
    interval = getattr(settings, 'POLLING_INTERVAL_SECONDS', 3600)
    batch_size = getattr(settings, 'POLLING_BATCH_SIZE', 10)
    
    logger.info("Configuration:")
    logger.info(f"  - Polling Interval: {interval}s ({interval/3600:.1f} hours)")
    logger.info(f"  - Batch Size: {batch_size} files")
    logger.info(f"  - Database: {settings.DATABASE_URL[:50]}...")
    logger.info("")
    
    # Create polling service
    service = PollingService(
        polling_interval_seconds=interval,
        batch_size=batch_size,
        processing_timeout_hours=2
    )
    
    try:
        # Run polling loop
        asyncio.run(service.start_polling())
        
    except KeyboardInterrupt:
        logger.info("\n" + "=" * 60)
        logger.info("🛑 Received shutdown signal (Ctrl+C)")
        logger.info("=" * 60)
        service.stop_polling()
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        return 1
    
    logger.info("✅ Polling service stopped cleanly")
    return 0


if __name__ == "__main__":
    exit(main())