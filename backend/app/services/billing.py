from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.models.room import Room
from app.models.property import Property
from app.models.lease import Lease
from app.models.billing import ElectricityReading, CustomCharge, Invoice
from app.schemas.billing import RentCalculationPreview
from app.schemas.room import RoomResponse
from app.services.dates import due_datetime_for_reference

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
    total_due = room.basic_rent_amount + room.water_charge + room.cleaning_charge + room.other_charges + electricity_cost + custom_total
    
    return RentCalculationPreview(
        room_id=room.id,
        basic_rent=room.basic_rent_amount,
        water_charge=room.water_charge,
        cleaning_charge=room.cleaning_charge,
        other_charges=room.other_charges,
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

    property_query = await db.execute(select(Property).where(Property.id == property_id))
    property_obj = property_query.scalars().first()
    if not property_obj:
        raise ValueError("Property not found")

    preview = await calculate_room_rent(db, property_id, room_id)
    
    now = datetime.now(timezone.utc)
    # Billing cycle is for the past month, and invoice due date follows the property's configured due day.
    billing_start = (now.replace(day=1) - timedelta(days=1)).replace(day=1) 
    billing_end = now
    due_date = due_datetime_for_reference(now, property_obj.billing_due_date or 1)

    invoice = Invoice(
        tenant_id=lease.tenant_id,
        room_id=room_id,
        billing_cycle_start=billing_start,
        billing_cycle_end=billing_end,
        due_date=due_date,
        basic_rent=preview.basic_rent,
        water_charge=preview.water_charge,
        cleaning_charge=preview.cleaning_charge,
        other_charges=preview.other_charges,
        electricity_charge=preview.electricity_cost,
        custom_charges_total=sum(c["amount"] for c in preview.custom_charges),
        total_amount_due=preview.total_due,
        status="pending"
    )
    
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    return invoice

async def enrich_room_billing(db: AsyncSession, room: Room, property_obj: Property) -> RoomResponse:
    try:
        # 1. Determine cycle cutoff based on billing_due_date
        now = datetime.now(timezone.utc)
        due_day = property_obj.billing_due_date or 1
        
        # Calculate the most recent cutoff date
        if now.day > due_day:
            cutoff = now.replace(day=due_day, hour=23, minute=59, second=59, microsecond=0)
        else:
            # Previous month cutoff
            first_of_month = now.replace(day=1)
            last_day_prev = first_of_month - timedelta(days=1)
            # Handle months with fewer days than due_day
            target_day = min(due_day, last_day_prev.day)
            cutoff = last_day_prev.replace(day=target_day, hour=23, minute=59, second=59, microsecond=0)

        # 2. Fetch readings to identify current and last for the active cycle
        readings_query = await db.execute(
            select(ElectricityReading)
            .where(ElectricityReading.room_id == room.id)
            .order_by(desc(ElectricityReading.reading_date))
            .limit(3) # Fetch enough to find the one before the cutoff
        )
        readings = readings_query.scalars().all()
        
        if readings:
            # Ensure reading_date is timezone-aware for comparison
            r0_date = readings[0].reading_date
            if r0_date.tzinfo is None:
                r0_date = r0_date.replace(tzinfo=timezone.utc)

            if r0_date > cutoff:
                # We have a reading in the current cycle
                current_reading = readings[0].reading_units
                # Find the most recent reading <= cutoff as the reference
                last_reading = None
                for r in readings[1:]:
                    r_date = r.reading_date
                    if r_date.tzinfo is None:
                        r_date = r_date.replace(tzinfo=timezone.utc)
                    if r_date <= cutoff:
                        last_reading = r.reading_units
                        break
                
                # FALLBACK: If we have multiple readings but none are <= cutoff,
                # use the one immediately before the current one.
                # This handles 'first-time' setup where the user enters both today.
                if last_reading is None and len(readings) > 1:
                    last_reading = readings[1].reading_units
                
                # If we STILL have no last reading (only 1 reading ever available)
                if last_reading is None:
                    last_reading = current_reading
                    units_consumed = 0.0
                else:
                    units_consumed = max(0, current_reading - last_reading)
            else:
                # The most recent reading is OLD (before cutoff). 
                # It should be treated as the 'Last Reading' for the upcoming/current cycle.
                last_reading = readings[0].reading_units
                current_reading = None
                units_consumed = 0.0
        else:
            # No readings at all
            current_reading = None
            last_reading = None
            units_consumed = 0.0
        
        elec_cost = units_consumed * (property_obj.electricity_per_unit_cost or 0)
        
        total_rent = (room.basic_rent_amount or 0) + \
                     (room.water_charge or 0) + \
                     (room.cleaning_charge or 0) + \
                     (room.other_charges or 0) + \
                     elec_cost
        
        resp = RoomResponse.model_validate(room)
        resp.current_electricity_cost = elec_cost
        resp.current_reading = current_reading
        resp.last_reading = last_reading
        resp.last_units_consumed = units_consumed
        resp.total_monthly_rent = total_rent
        return resp
    except Exception as e:
        print(f"Error in enrich_room_billing for room {room.id}: {e}")
        import traceback
        traceback.print_exc()
        raise e
