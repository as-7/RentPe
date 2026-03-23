import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.future import select

from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.models.room import Room
from app.services.billing import generate_invoice_for_room
from app.services.reminders import send_due_date_reminders
from app.services.dates import get_app_timezone

logger = logging.getLogger(__name__)

async def automated_monthly_invoicing():
    """
    Cron job triggered on the 1st of every month to compute
    and generate invoices for all rooms.
    """
    logger.info("Starting automated monthly rent calculation & invoicing...")
    async with AsyncSessionLocal() as db:
        rooms_query = await db.execute(select(Room).where(Room.is_vacant == False))
        rooms = rooms_query.scalars().all()
        
        for room in rooms:
            try:
                # Assuming the landlord/system generates for the specific property
                invoice = await generate_invoice_for_room(db, property_id=room.property_id, room_id=room.id)
                if invoice:
                    logger.info(f"Generated invoice for Room {room.id} -> Total Due: {invoice.total_amount_due}")
            except Exception as e:
                logger.error(f"Failed to generate invoice for Room {room.id}: {e}")

async def automated_due_date_reminders():
    logger.info("Starting automated WhatsApp due-date reminder run...")
    async with AsyncSessionLocal() as db:
        summary = await send_due_date_reminders(db)
        logger.info(
            "WhatsApp reminders finished. Attempted=%s Sent=%s Skipped=%s Failures=%s",
            summary["attempted"],
            summary["sent"],
            summary["skipped"],
            len(summary["failures"]),
        )


scheduler = AsyncIOScheduler(timezone=get_app_timezone())

def start_scheduler():
    if scheduler.running:
        return

    # Schedule to run on the 1st day of every month at midnight
    scheduler.add_job(
        automated_monthly_invoicing,
        'cron',
        id='monthly_invoicing',
        day='1',
        hour='0',
        minute='0',
        replace_existing=True,
    )
    scheduler.add_job(
        automated_due_date_reminders,
        'cron',
        id='daily_due_date_reminders',
        hour=str(settings.WHATSAPP_REMINDER_HOUR),
        minute=str(settings.WHATSAPP_REMINDER_MINUTE),
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Automated schedulers started.")
