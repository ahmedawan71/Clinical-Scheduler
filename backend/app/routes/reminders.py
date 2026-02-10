from fastapi import APIRouter, BackgroundTasks, Depends
from app.agents.reminder_agent import send_appointment_reminders, get_pending_reminders
from app.utils.logger import agent_logger

router = APIRouter()

@router.post("/send")
async def trigger_reminders(background_tasks: BackgroundTasks, hours_before: int = 24):
    """
    Trigger reminder sending.
    Call this endpoint via cron job or scheduled task.
    """
    background_tasks.add_task(send_appointment_reminders, hours_before)
    agent_logger.info(f"Reminder job triggered for {hours_before} hours ahead")
    return {
        "status": "started",
        "hours_before": hours_before,
        "message": "Reminder job running in background"
    }

@router.get("/pending")
async def get_pending():
    """Get appointments pending reminders"""
    return get_pending_reminders()

@router.post("/send-now")
async def send_reminders_sync(hours_before: int = 24):
    """Send reminders synchronously (for testing)"""
    result = await send_appointment_reminders(hours_before)
    return result