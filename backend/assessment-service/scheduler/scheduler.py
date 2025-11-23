from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from services.assessment_service import AssessmentService
from config.settings import settings
from config.logger import logger, log_scheduler_run
from datetime import datetime
import asyncio


DAILY_SCHEDULE = "daily at 02:00 AM"


class AssessmentScheduler:
    """Scheduler for periodic assessment checks"""
    
    def __init__(self):
        """Initialize scheduler"""
        self.scheduler = AsyncIOScheduler()
        self.assessment_service = AssessmentService()
        self.is_running = False
    
    def start(self):
        """Start the scheduler"""
        if self.is_running:
            print("⚠️ Scheduler already running")
            return
        
        # Job: Assessment check - runs once daily at 2 AM
        self.scheduler.add_job(
            func=self._run_assessment_check,
            trigger=CronTrigger(hour=2, minute=0),  # 2:00 AM every day
            id='assessment_check',
            name='Check for completed interviews and generate assessments',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        
        logger.info(
            "scheduler_started",
            schedule=DAILY_SCHEDULE,
            grace_period_minutes=settings.assessment_grace_period_minutes
        )
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            return
        
        self.scheduler.shutdown(wait=True)
        self.is_running = False
        logger.info("scheduler_stopped")
    
    def get_status(self) -> dict:
        """Get scheduler status"""
        if not self.is_running:
            return {
                "running": False,
                "next_run": None,
                "schedule": DAILY_SCHEDULE
            }

        jobs = self.scheduler.get_jobs()
        if jobs:
            job = jobs[0]
            return {
                "running": True,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "schedule": DAILY_SCHEDULE,
                "job_id": job.id,
                "job_name": job.name
            }

        return {
            "running": True,
            "next_run": None,
            "schedule": DAILY_SCHEDULE
        }
    
    async def _run_assessment_check(self):
        """
        Background job that runs every 10 minutes
        Checks for completed interviews and generates assessments
        """
        logger.info("scheduler_check_started", timestamp=datetime.now().isoformat())
        
        try:
            import sys
            sys.path.append('/common-service')
            
            from db import UnitOfWork
            from repositories.assessment_repository import AssessmentRepository
            
            # Find ready interviews
            with UnitOfWork() as uow:
                repo = AssessmentRepository(uow)
                
                # Get completed interviews without assessments
                ready_interviews = repo.get_completed_interviews_without_assessment(limit=10)
                
                if not ready_interviews:
                    logger.info("no_interviews_ready")
                    return
                
                logger.info("interviews_found", count=len(ready_interviews))
            
            # Process each interview
            processed_count = 0
            skipped_count = 0
            error_count = 0
            
            for interview in ready_interviews:
                interview_id = str(interview['id'])
                
                try:
                    logger.info("processing_interview", interview_id=interview_id)
                    
                    # Generate assessment
                    result = await self.assessment_service.generate_assessment(interview_id)
                    
                    if result['status'] == 'success':
                        processed_count += 1
                    elif result['status'] == 'incomplete':
                        skipped_count += 1
                    elif result['status'] == 'already_exists':
                        skipped_count += 1
                    else:
                        error_count += 1
                
                except Exception as e:
                    error_count += 1
                    logger.error("interview_processing_exception", interview_id=interview_id, error=str(e))
                    import traceback
                    traceback.print_exc()
            
            # Summary
            log_scheduler_run(
                interviews_found=len(ready_interviews),
                processed=processed_count,
                skipped=skipped_count,
                errors=error_count
            )
        
        except Exception as e:
            logger.error("scheduler_check_fatal_error", error=str(e))
            import traceback
            traceback.print_exc()
    
    async def run_manual_check(self):
        """Manually trigger an assessment check (for testing/debugging)"""
        logger.info("manual_check_triggered")
        await self._run_assessment_check()


# Global scheduler instance
assessment_scheduler = AssessmentScheduler()