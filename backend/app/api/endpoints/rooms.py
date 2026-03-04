from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.room import Room as RoomModel
from app.models.property import Property as PropertyModel
from app.models.user import User as UserModel
from app.api.deps import get_current_user
from app.services.billing import enrich_room_billing
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
    
    # Fetch property for enrichment
    prop_result = await db.execute(select(PropertyModel).where(PropertyModel.id == db_room.property_id))
    prop = prop_result.scalars().first()
    
    return await enrich_room_billing(db, db_room, prop)

@router.get("/property/{property_id}", response_model=List[RoomResponse])
async def read_rooms_by_property(property_id: int, skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    # Fetch property for electricity cost
    prop_result = await db.execute(select(PropertyModel).where(PropertyModel.id == property_id))
    property_obj = prop_result.scalars().first()
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")

    result = await db.execute(select(RoomModel).where(RoomModel.property_id == property_id).offset(skip).limit(limit))
    rooms = result.scalars().all()
    
    room_responses = []
    for room in rooms:
        room_responses.append(await enrich_room_billing(db, room, property_obj))
        
    return room_responses

@router.get("/{room_id}", response_model=RoomResponse)
async def read_room(room_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RoomModel).where(RoomModel.id == room_id))
    db_room = result.scalars().first()
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")
        
    prop_result = await db.execute(select(PropertyModel).where(PropertyModel.id == db_room.property_id))
    prop = prop_result.scalars().first()
    
    return await enrich_room_billing(db, db_room, prop)

@router.put("/{room_id}", response_model=RoomResponse)
async def update_room(room_id: int, room_in: RoomUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RoomModel).where(RoomModel.id == room_id))
    db_room = result.scalars().first()
    if not db_room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    update_data = room_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_room, key, value)
    
    await db.commit()
    await db.refresh(db_room)
    
    # Fetch property for enrichment
    prop_result = await db.execute(select(PropertyModel).where(PropertyModel.id == db_room.property_id))
    prop = prop_result.scalars().first()
    
    return await enrich_room_billing(db, db_room, prop)
