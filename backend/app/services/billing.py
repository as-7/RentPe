from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from datetime import datetime, timedelta
from typing import Optional

from app.models.room import Room
from app.models.property import Property
from app.models.lease import Lease
from app.models.billing import ElectricityReading, CustomCharge, Invoice
from app.schemas.billing import RentCalculationPreview

async def calculate_room_rent(db: AsyncSession, property_id: int, room_id: int) -> RentCalculationPreview:
    # 1. Fetch Property and Room
    room_query = await db.execute(select(Room).where(Room.id == room_id, Room.property_id == property_id))
    room = room_query.scalars().first()
    
    if not room:
        raise ValueError("Room not found")
        
    prop_query = await db.execute(select(Property).where(Property.id == property_id))
    property_obj = prop_query.scalars().first()

    # 2. Electricity Calculation
    # Fetch top 2 most recent readings
    readings_query = await db.execute(
        select(ElectricityReading)
        .where(ElectricityReading.room_id == room_id)
        .order_by(desc(ElectricityReading.reading_date))
        .limit(2)
    )
    readings = readings_query.scalars().all()
    
    units_consumed = 0.0
    if len(readings) == 2:
        units_consumed = readings[0].reading_units - readings[1].reading_units
    elif len(readings) == 1:
        # First reading recorded, assume starting from 0 or it's the base reading
        units_consumed = 0.0 # Standard policy until a full cycle completes
        
    electricity_cost = units_consumed * property_obj.electricity_per_unit_cost

    # 3. Custom Charges
    charges_query = await db.execute(
        select(CustomCharge)
        .where(CustomCharge.room_id == room_id, CustomCharge.is_recurring == True)
    )
    custom_charges = charges_query.scalars().all()
    custom_total = sum(charge.amount for charge in custom_charges)

    # 4. Total Calculation
    total_due = room.basic_rent_amount + room.water_charge + electricity_cost + custom_total
    
    return RentCalculationPreview(
        room_id=room.id,
        basic_rent=room.basic_rent_amount,
        water_charge=room.water_charge,
        electricity_units_consumed=units_consumed,
        electricity_cost=electricity_cost,
        custom_charges=[{"id": c.id, "room_id": c.room_id, "charge_name": c.charge_name, "amount": c.amount, "is_recurring": c.is_recurring} for c in custom_charges],
        total_due=total_due
    )


async def generate_invoice_for_room(db: AsyncSession, property_id: int, room_id: int) -> Optional[Invoice]:
    # Check for active lease
    lease_query = await db.execute(
        select(Lease)
        .where(Lease.room_id == room_id, Lease.is_active == True)
    )
    lease = lease_query.scalars().first()
    
    if not lease:
        return None  # Room is vacant, no invoice needed
        
    preview = await calculate_room_rent(db, property_id, room_id)
    
    now = datetime.utcnow()
    # Simple logic: billing cycle is for the past month, due date is 5 days from generation
    billing_start = (now.replace(day=1) - timedelta(days=1)).replace(day=1) 
    billing_end = now
    due_date = now + timedelta(days=5)

    invoice = Invoice(
        tenant_id=lease.tenant_id,
        room_id=room_id,
        billing_cycle_start=billing_start,
        billing_cycle_end=billing_end,
        due_date=due_date,
        basic_rent=preview.basic_rent,
        water_charge=preview.water_charge,
        electricity_charge=preview.electricity_cost,
        custom_charges_total=sum(c["amount"] for c in preview.custom_charges),
        total_amount_due=preview.total_due,
        status="pending"
    )
    
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    return invoice
