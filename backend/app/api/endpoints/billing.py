from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.core.database import get_db
from app.models.billing import ElectricityReading as ElectricityModel, CustomCharge as ChargeModel
from app.schemas.billing import ElectricityReadingCreate, ElectricityReadingResponse, CustomChargeCreate, CustomChargeResponse, RentCalculationPreview, InvoiceResponse
from app.services.billing import calculate_room_rent, generate_invoice_for_room

router = APIRouter()

@router.post("/electricity", response_model=ElectricityReadingResponse)
async def add_electricity_reading(reading_in: ElectricityReadingCreate, db: AsyncSession = Depends(get_db)):
    db_reading = ElectricityModel(**reading_in.model_dump())
    db.add(db_reading)
    await db.commit()
    await db.refresh(db_reading)
    return db_reading

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
