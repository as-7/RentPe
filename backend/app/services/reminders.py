from datetime import date
from typing import Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.billing import ReminderLog
from app.models.property import Property
from app.models.room import Room
from app.services.billing import calculate_room_rent
from app.services.dates import get_local_now, next_due_date
from app.services.whatsapp import (
    WhatsAppConfigurationError,
    WhatsAppSendError,
    is_configured as whatsapp_is_configured,
    send_template_message,
)


def get_reminder_offsets() -> List[int]:
    offsets: List[int] = []
    for value in settings.WHATSAPP_REMINDER_OFFSETS.split(","):
        cleaned = value.strip()
        if not cleaned:
            continue
        offsets.append(max(0, int(cleaned)))
    return sorted(set(offsets), reverse=True)


def build_reminder_parameters(room: Room, property_obj: Property, amount_due: float, due_date: date) -> List[str]:
    return [
        room.tenant_name or f"Tenant of Room {room.room_number}",
        property_obj.name,
        room.room_number,
        f"{amount_due:.2f}",
        due_date.strftime("%d %b %Y"),
    ]


async def already_sent_for_due_date(
    db: AsyncSession,
    property_id: int,
    room_id: int,
    due_date: date,
    days_before_due: int,
) -> bool:
    result = await db.execute(
        select(ReminderLog.id).where(
            and_(
                ReminderLog.property_id == property_id,
                ReminderLog.room_id == room_id,
                ReminderLog.target_due_date == due_date,
                ReminderLog.days_before_due == days_before_due,
                ReminderLog.status == "sent",
            )
        )
    )
    return result.scalar_one_or_none() is not None


async def send_due_date_reminders(
    db: AsyncSession,
    landlord_id: Optional[int] = None,
    property_id: Optional[int] = None,
) -> Dict[str, object]:
    if not settings.WHATSAPP_ENABLED:
        return {"attempted": 0, "sent": 0, "skipped": 0, "failures": [], "reason": "whatsapp_disabled"}
    if not whatsapp_is_configured():
        raise WhatsAppConfigurationError("WhatsApp is enabled but required settings are missing")

    now = get_local_now()
    today = now.date()
    offsets = get_reminder_offsets()

    stmt = select(Property)
    if landlord_id is not None:
        stmt = stmt.where(Property.landlord_id == landlord_id)
    if property_id is not None:
        stmt = stmt.where(Property.id == property_id)

    properties_result = await db.execute(stmt)
    properties = properties_result.scalars().all()

    attempted = 0
    sent = 0
    skipped = 0
    failures: List[Dict[str, object]] = []

    for property_obj in properties:
        due_date = next_due_date(today, property_obj.billing_due_date or 1)
        days_until_due = (due_date - today).days
        if days_until_due not in offsets:
            continue

        rooms_result = await db.execute(
            select(Room).where(
                Room.property_id == property_obj.id,
                Room.is_vacant == False,
                Room.tenant_mobile.is_not(None),
                Room.tenant_mobile != "",
            )
        )
        rooms = rooms_result.scalars().all()

        for room in rooms:
            if await already_sent_for_due_date(db, property_obj.id, room.id, due_date, days_until_due):
                skipped += 1
                continue

            attempted += 1
            try:
                preview = await calculate_room_rent(db, property_obj.id, room.id)
                provider_message_id = await send_template_message(
                    recipient_phone=room.tenant_mobile,
                    body_parameters=build_reminder_parameters(
                        room=room,
                        property_obj=property_obj,
                        amount_due=preview.total_due,
                        due_date=due_date,
                    ),
                )
                db.add(
                    ReminderLog(
                        property_id=property_obj.id,
                        room_id=room.id,
                        target_due_date=due_date,
                        days_before_due=days_until_due,
                        tenant_mobile=room.tenant_mobile,
                        status="sent",
                        provider_message_id=provider_message_id,
                    )
                )
                sent += 1
            except (ValueError, WhatsAppSendError) as exc:
                db.add(
                    ReminderLog(
                        property_id=property_obj.id,
                        room_id=room.id,
                        target_due_date=due_date,
                        days_before_due=days_until_due,
                        tenant_mobile=room.tenant_mobile,
                        status="failed",
                        error_message=str(exc)[:500],
                    )
                )
                failures.append(
                    {
                        "property_id": property_obj.id,
                        "room_id": room.id,
                        "mobile": room.tenant_mobile,
                        "error": str(exc),
                    }
                )

    await db.commit()
    return {"attempted": attempted, "sent": sent, "skipped": skipped, "failures": failures}
