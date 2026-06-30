import logging

from config.celery import app

logger = logging.getLogger(__name__)


@app.task(name="collections.run_daily_overdue_check")
def run_daily_overdue_check() -> dict:
    from .services import CollectionsService

    stats = CollectionsService().run_daily_overdue_check()
    logger.info("collections_task_done", extra=stats)
    return stats


@app.task(name="collections.run_due_soon_reminders")
def run_due_soon_reminders() -> dict:
    from .services import CollectionsService

    sent = CollectionsService().run_due_soon_reminders()
    logger.info("due_soon_reminders_sent", extra={"count": sent})
    return {"sent": sent}
