import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.future import select

from app.core.database import AsyncSessionLocal
from app.models.room import Room
from app.models.property import Property
from app.services.billing import generate_invoice_for_room

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

scheduler = AsyncIOScheduler()

def start_scheduler():
    # Schedule to run on the 1st day of every month at midnight
    scheduler.add_job(automated_monthly_invoicing, 'cron', day='1', hour='0', minute='0')
    scheduler.start()
    logger.info("Automated invoice scheduler started.")
