from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List

from app.core.database import get_db
from app.models.property import Property as PropertyModel
from app.models.room import Room as RoomModel
from app.models.user import User as UserModel
from app.api.deps import get_current_user
from app.services.billing import enrich_room_billing
from app.schemas.property import PropertyCreate, PropertyUpdate, PropertyResponse, PropertyBulkCreate

router = APIRouter()

@router.post("/", response_model=PropertyResponse)
async def create_property(property_in: PropertyCreate, db: AsyncSession = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    db_property = PropertyModel(**property_in.model_dump(), landlord_id=current_user.id)
    db.add(db_property)
    await db.commit()
    await db.refresh(db_property)
    
    # Newly created property has 0 rooms
    response = PropertyResponse.model_validate(db_property)
    response.total_rooms = 0
    response.vacant_rooms = 0
    return response

@router.post("/bulk-create", response_model=PropertyResponse)
async def bulk_create_property(property_in: PropertyBulkCreate, db: AsyncSession = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    # Create the Property
    # We take the defaults from the first group or a default 0.0
    first_group = property_in.room_groups[0] if property_in.room_groups else None
    db_property = PropertyModel(
        name=property_in.name,
        address=property_in.address,
        electricity_per_unit_cost=property_in.electricity_per_unit_cost,
        water_charge=first_group.water if first_group else 0.0,
        cleaning_charge=first_group.cleaning if first_group else 0.0,
        other_charges=first_group.other if first_group else 0.0,
        landlord_id=current_user.id
    )
    db.add(db_property)
    await db.flush() # Flush to get the property ID before committing
    
    # Create Rooms by Group
    rooms_to_create = []
    current_room_num = 1
    
    for group in property_in.room_groups:
        for i in range(group.count):
            # If occupied_count is 0, we default to ALL occupied as per previous user preference
            # unless they specifically start using occupied_count > 0 in which case we follow that.
            # Let's assume if occupied_count is 0, they want ALL occupied.
            # Otherwise, first N are occupied.
            is_vacant = False
            if group.occupied_count > 0:
                is_vacant = True if (i + 1) > group.occupied_count else False
            
            room = RoomModel(
                room_number=f"{current_room_num}",
                basic_rent_amount=group.rent,
                water_charge=group.water,
                cleaning_charge=group.cleaning,
                other_charges=group.other,
                is_vacant=is_vacant,
                property_id=db_property.id
            )
            rooms_to_create.append(room)
            current_room_num += 1
        
    db.add_all(rooms_to_create)
    await db.commit()
    
    # Eagerly load the property with its new rooms to avoid Pydantic MissingGreenlet error
    result = await db.execute(
        select(PropertyModel)
        .options(selectinload(PropertyModel.rooms))
        .where(PropertyModel.id == db_property.id)
    )
    db_property_reloaded = result.scalars().first()
    
    response = PropertyResponse.model_validate(db_property_reloaded)
    response.total_rooms = len(rooms_to_create)
    response.vacant_rooms = sum(1 for r in rooms_to_create if r.is_vacant)
    return response

@router.get("/", response_model=List[PropertyResponse])
async def read_properties(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    result = await db.execute(
        select(PropertyModel)
        .options(selectinload(PropertyModel.rooms))
        .where(PropertyModel.landlord_id == current_user.id)
        .offset(skip).limit(limit)
    )
    properties = result.scalars().all()
    
    response_list = []
    for prop in properties:
        rooms_result = await db.execute(select(RoomModel).where(RoomModel.property_id == prop.id))
        rooms = rooms_result.scalars().all()
        
        prop_resp = PropertyResponse.model_validate(prop)
        prop_resp.total_rooms = len(rooms)
        prop_resp.vacant_rooms = sum(1 for r in rooms if r.is_vacant)
        
        enriched_rooms = []
        for r in rooms:
            enriched_rooms.append(await enrich_room_billing(db, r, prop))
        prop_resp.rooms = enriched_rooms
        
        response_list.append(prop_resp)
        
    return response_list

@router.get("/{property_id}", response_model=PropertyResponse)
async def read_property(property_id: int, db: AsyncSession = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    result = await db.execute(
        select(PropertyModel)
        .options(selectinload(PropertyModel.rooms))
        .where(PropertyModel.id == property_id, PropertyModel.landlord_id == current_user.id)
    )
    db_property = result.scalars().first()
    if not db_property:
        raise HTTPException(status_code=404, detail="Property not found")
    
    rooms_result = await db.execute(select(RoomModel).where(RoomModel.property_id == db_property.id))
    rooms = rooms_result.scalars().all()
    
    response = PropertyResponse.model_validate(db_property)
    response.total_rooms = len(rooms)
    response.vacant_rooms = sum(1 for r in rooms if r.is_vacant)
    
    enriched_rooms = []
    for r in rooms:
        enriched_rooms.append(await enrich_room_billing(db, r, db_property))
    response.rooms = enriched_rooms
    
    return response

@router.put("/{property_id}", response_model=PropertyResponse)
async def update_property(property_id: int, property_in: PropertyUpdate, db: AsyncSession = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    result = await db.execute(select(PropertyModel).where(PropertyModel.id == property_id, PropertyModel.landlord_id == current_user.id))
    db_property = result.scalars().first()
    if not db_property:
        raise HTTPException(status_code=404, detail="Property not found")
    
    update_data = property_in.model_dump(exclude_unset=True)
    
    # Track if we need to update all rooms
    propagate_fields = ["water_charge", "cleaning_charge", "other_charges"]
    should_propagate = any(field in update_data for field in propagate_fields)
    
    for key, value in update_data.items():
        setattr(db_property, key, value)
    
    if should_propagate:
        # Update all rooms in this property with the new defaults
        from sqlalchemy import update
        room_updates = {}
        if "water_charge" in update_data:
            room_updates[RoomModel.water_charge] = update_data["water_charge"]
        if "cleaning_charge" in update_data:
            room_updates[RoomModel.cleaning_charge] = update_data["cleaning_charge"]
        if "other_charges" in update_data:
            room_updates[RoomModel.other_charges] = update_data["other_charges"]
            
        await db.execute(
            update(RoomModel)
            .where(RoomModel.property_id == property_id)
            .values(room_updates)
        )
    
    await db.commit()
    
    # Re-fetch with rooms pre-loaded (same as read_property)
    result2 = await db.execute(
        select(PropertyModel)
        .options(selectinload(PropertyModel.rooms))
        .where(PropertyModel.id == property_id)
    )
    db_property = result2.scalars().first()
    
    rooms_result = await db.execute(select(RoomModel).where(RoomModel.property_id == property_id))
    rooms = rooms_result.scalars().all()
    
    response = PropertyResponse.model_validate(db_property)
    response.total_rooms = len(rooms)
    response.vacant_rooms = sum(1 for r in rooms if r.is_vacant)
    
    enriched_rooms = []
    for r in rooms:
        enriched_rooms.append(await enrich_room_billing(db, r, db_property))
    response.rooms = enriched_rooms
    
    return response

@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property(property_id: int, db: AsyncSession = Depends(get_db), current_user: UserModel = Depends(get_current_user)):
    result = await db.execute(select(PropertyModel).where(PropertyModel.id == property_id, PropertyModel.landlord_id == current_user.id))
    db_property = result.scalars().first()
    if not db_property:
        raise HTTPException(status_code=404, detail="Property not found")
    
    await db.delete(db_property)
    await db.commit()
    return None
