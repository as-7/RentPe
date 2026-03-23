from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import desc, select
from typing import List, Optional

from app.core.database import get_db
from app.models.billing import ElectricityReading as ElectricityModel, CustomCharge as ChargeModel
from app.models.property import Property as PropertyModel
from app.models.user import User as UserModel
from app.api.deps import get_current_user
from app.schemas.billing import ElectricityReadingCreate, ElectricityReadingResponse, CustomChargeCreate, CustomChargeResponse, RentCalculationPreview, InvoiceResponse
from app.services.billing import calculate_room_rent, generate_invoice_for_room
from app.services.reminders import send_due_date_reminders

router = APIRouter()

@router.post("/electricity", response_model=ElectricityReadingResponse)
async def add_electricity_reading(reading_in: ElectricityReadingCreate, db: AsyncSession = Depends(get_db)):
    db_reading = ElectricityModel(**reading_in.model_dump())
    db.add(db_reading)
    await db.commit()
    await db.refresh(db_reading)
    return db_reading

@router.put("/electricity/{reading_id}", response_model=ElectricityReadingResponse)
async def update_electricity_reading(reading_id: int, reading_in: ElectricityReadingCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ElectricityModel).where(ElectricityModel.id == reading_id))
    db_reading = result.scalars().first()
    if not db_reading:
        raise HTTPException(status_code=404, detail="Reading not found")
    
    update_data = reading_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_reading, key, value)
    
    await db.commit()
    await db.refresh(db_reading)
    return db_reading

@router.get("/electricity/latest/{room_id}", response_model=Optional[ElectricityReadingResponse])
async def get_latest_electricity_reading(room_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ElectricityModel)
        .where(ElectricityModel.room_id == room_id)
        .order_by(desc(ElectricityModel.reading_date))
        .limit(1)
    )
    return result.scalars().first()

@router.post("/charges", response_model=CustomChargeResponse)
async def add_custom_charge(charge_in: CustomChargeCreate, db: AsyncSession = Depends(get_db)):
    db_charge = ChargeModel(**charge_in.model_dump())
    db.add(db_charge)
    await db.commit()
    await db.refresh(db_charge)
    return db_charge

@router.get("/preview/{property_id}/{room_id}", response_model=RentCalculationPreview)
async def preview_rent(property_id: int, room_id: int, db: AsyncSession = Depends(get_db)):
    try:
        preview = await calculate_room_rent(db, property_id, room_id)
        return preview
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/generate-invoice/{property_id}/{room_id}", response_model=InvoiceResponse)
async def generate_invoice(property_id: int, room_id: int, db: AsyncSession = Depends(get_db)):
    try:
        invoice = await generate_invoice_for_room(db, property_id, room_id)
        if not invoice:
            raise HTTPException(status_code=400, detail="Room has no active lease or is vacant.")
        return invoice
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/reminders/send")
async def send_whatsapp_reminders(
    property_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    if property_id is not None:
        property_result = await db.execute(
            select(PropertyModel).where(
                PropertyModel.id == property_id,
                PropertyModel.landlord_id == current_user.id,
            )
        )
        property_obj = property_result.scalars().first()
        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")

    try:
        return await send_due_date_reminders(db, landlord_id=current_user.id, property_id=property_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
