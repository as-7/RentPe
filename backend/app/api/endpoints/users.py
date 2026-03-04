from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user import User as UserModel
from app.models.property import Property as PropertyModel
from app.models.room import Room as RoomModel
from app.models.lease import Lease as LeaseModel
from app.models.billing import Invoice as InvoiceModel
from app.schemas.user import UserResponse, UserCreate
from app.services.auth import create_access_token, verify_firebase_token
from app.api.deps import get_current_user
from sqlalchemy import func

router = APIRouter()

class FirebaseTokenRequest(BaseModel):
    token: str

@router.post("/verify-firebase")
async def verify_firebase(request: FirebaseTokenRequest, db: AsyncSession = Depends(get_db)):
    # 1. Verify the ID Token with Firebase Admin SDK
    decoded_token = verify_firebase_token(request.token)
    
    if not decoded_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase Auth token"
        )
    
    # 2. Extract user details from Firebase token
    firebase_uid = decoded_token.get("uid")
    phone_number = decoded_token.get("phone_number")
    email = decoded_token.get("email")

    if not firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Firebase token missing uid"
        )
    
    # 3. Check if user exists by firebase_uid
    result = await db.execute(select(UserModel).where(UserModel.firebase_uid == firebase_uid))
    user = result.scalars().first()

    # Fallback to checking by phone_number if they existed before we added firebase_uid
    if not user and phone_number:
        result = await db.execute(select(UserModel).where(UserModel.phone_number == phone_number))
        user = result.scalars().first()
        if user:
            # Update legacy user with their new firebase_uid
            user.firebase_uid = firebase_uid
            await db.commit()
    
    # Generate user if doesn't exist
    if not user:
        user = UserModel(
            firebase_uid=firebase_uid,
            phone_number=phone_number,
            email=email
        )
        db.add(user)
        try:
            await db.commit()
            await db.refresh(user)
        except Exception as e:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create user: {str(e)}"
            )

    # 4. Issue standard local JWT Token for API session
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id}

@router.get("/me", response_model=UserResponse)
async def read_users_me(db: AsyncSession = Depends(get_db)):
    # TODO: get current user from token scope and inject via FastApi Depends
    return {"phone_number": "mocked", "id": 1, "is_active": True, "created_at": "2024-01-01T00:00:00Z"}

@router.get("/dashboard")
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    # Base query for user's properties
    user_properties_stmt = select(PropertyModel.id).where(PropertyModel.landlord_id == current_user.id)
    user_property_ids = (await db.execute(user_properties_stmt)).scalars().all()

    if not user_property_ids:
        return {
            "total_buildings": 0,
            "total_rent": 0,
            "occupied_rooms": 0,
            "empty_rooms": 0,
            "has_properties": False,
            "recent_activity": []
        }

    total_buildings = len(user_property_ids)

    # Empty Rooms
    empty_rooms_stmt = select(func.count(RoomModel.id)).where(
        RoomModel.property_id.in_(user_property_ids),
        RoomModel.is_vacant == True
    )
    empty_rooms = (await db.execute(empty_rooms_stmt)).scalar() or 0

    # Occupied Rooms
    occupied_rooms_stmt = select(func.count(RoomModel.id)).where(
        RoomModel.property_id.in_(user_property_ids),
        RoomModel.is_vacant == False
    )
    occupied_rooms = (await db.execute(occupied_rooms_stmt)).scalar() or 0

    # Total Rent (Expected Monthly Rent from Occupied Rooms)
    rent_stmt = select(
        func.sum(
            RoomModel.basic_rent_amount + 
            RoomModel.water_charge + 
            RoomModel.cleaning_charge + 
            RoomModel.other_charges
        )
    ).where(
        RoomModel.property_id.in_(user_property_ids),
        RoomModel.is_vacant == False
    )
    total_rent = (await db.execute(rent_stmt)).scalar() or 0

    # Recent Activity (Latest 3 Invoices logic for now, as activity example)
    recent_activity_stmt = select(InvoiceModel).join(RoomModel).where(
        RoomModel.property_id.in_(user_property_ids)
    ).order_by(InvoiceModel.created_at.desc()).limit(3)
    recent_invoices = (await db.execute(recent_activity_stmt)).scalars().all()
    
    activity_list = []
    for inv in recent_invoices:
         activity_list.append({
             "id": inv.id,
             "title": f"Invoice {inv.status.capitalize()}",
             "description": f"Room ID {inv.room_id}",
             "amount": f"₹{inv.total_amount_due}",
             "type": "invoice",
             "date": inv.created_at.isoformat() if inv.created_at else None
         })

    # Fetch Properties
    properties = (await db.execute(select(PropertyModel).where(PropertyModel.landlord_id == current_user.id))).scalars().all()
    properties_list = []
    for p in properties:
        r_stmt = select(RoomModel).where(RoomModel.property_id == p.id)
        r_all = (await db.execute(r_stmt)).scalars().all()
        properties_list.append({
            "id": p.id,
            "name": p.name,
            "address": p.address,
            "total_rooms": len(r_all),
            "vacant_rooms": sum(1 for r in r_all if r.is_vacant)
        })

    return {
        "total_buildings": total_buildings,
        "total_rent": total_rent,
        "occupied_rooms": occupied_rooms,
        "empty_rooms": empty_rooms,
        "has_properties": True,
        "recent_activity": activity_list,
        "properties": properties_list
    }


