from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.core.database import get_db
from app.models.room import Room as RoomModel
from app.models.property import Property as PropertyModel
from app.schemas.room import RoomCreate, RoomUpdate, RoomResponse

router = APIRouter()

@router.post("/", response_model=RoomResponse)
async def create_room(room_in: RoomCreate, db: AsyncSession = Depends(get_db)):
    # Verify property exists
    result = await db.execute(select(PropertyModel).where(PropertyModel.id == room_in.property_id))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Property not found")
        
    db_room = RoomModel(**room_in.model_dump())
    db.add(db_room)
    await db.commit()
    await db.refresh(db_room)
    return db_room

@router.get("/property/{property_id}", response_model=List[RoomResponse])
async def read_rooms_by_property(property_id: int, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RoomModel).where(RoomModel.property_id == property_id).offset(skip).limit(limit))
    return result.scalars().all()

@router.get("/{room_id}", response_model=RoomResponse)
async def read_room(room_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RoomModel).where(RoomModel.id == room_id))
    db_room = result.scalars().first()
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")
    return db_room
