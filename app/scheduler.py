import logging 
from apscheduler.schedulers.background import BackgroundScheduler

from app.database import SessionLocal
from app.services.recurring_service import process_due_recurring_transactions

logger=logging.getLogger(__name__)

scheduler=BackgroundScheduler(timezone="Asia/Kolkata")

def process_recurring_job():
    db=SessionLocal()

    try:
        result=process_due_recurring_transactions(db=db)
        logger.info(
            "Recurring transaction job completed: %s",
            result
        )

    except Exception:
        logger.exception(
            "Recurring transaction job failed"
        )

    finally:
        db.close()

def start_scheduler():
    scheduler.add_job(
        process_recurring_job,
        trigger="cron",
        hour=0,
        minute=5,
        id="process_recurring_transactions",
        replace_existing=True,
        coalesce=True,
        max_instances=1
    )

    scheduler.start()

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)

