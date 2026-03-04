from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.core.database import get_db
from app.models.property import Property as PropertyModel
from app.schemas.property import PropertyCreate, PropertyUpdate, PropertyResponse

router = APIRouter()

@router.post("/", response_model=PropertyResponse)
async def create_property(property_in: PropertyCreate, db: AsyncSession = Depends(get_db)):
    # Assuming authenticated landlord ID is injected. Hardcoding 1 for now.
    landlord_id = 1 
    
    db_property = PropertyModel(**property_in.model_dump(), landlord_id=landlord_id)
    db.add(db_property)
    await db.commit()
    await db.refresh(db_property)
    return db_property

@router.get("/", response_model=List[PropertyResponse])
async def read_properties(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PropertyModel).offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/{property_id}", response_model=PropertyResponse)
async def read_property(property_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PropertyModel).where(PropertyModel.id == property_id))
    db_property = result.scalars().first()
    if not db_property:
        raise HTTPException(status_code=404, detail="Property not found")
    return db_property
