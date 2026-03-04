from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel

from app.core.database import get_db
from app.models.user import User as UserModel
from app.schemas.user import UserResponse, UserCreate
from app.services.auth import create_access_token, verify_firebase_token

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
    
    # 2. Extract phone number confirmed by Firebase
    phone_number = decoded_token.get("phone_number")
    if not phone_number:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Firebase token didn't carry a verified phone number"
        )
    
    # 3. Check if user exists in our DB, else create them automatically (Sign-Up / Log-in)
    result = await db.execute(select(UserModel).where(UserModel.phone_number == phone_number))
    user = result.scalars().first()
    
    if not user:
        user = UserModel(phone_number=phone_number)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # 4. Issue standard local JWT Token for API session
    access_token = create_access_token(data={"sub": str(user.id), "role": user.role})
    
    return {"access_token": access_token, "token_type": "bearer", "user_id": user.id}

@router.get("/me", response_model=UserResponse)
async def read_users_me(db: AsyncSession = Depends(get_db)):
    # TODO: get current user from token scope and inject via FastApi Depends
    return {"phone_number": "mocked", "id": 1, "is_active": True, "created_at": "2024-01-01T00:00:00Z"}

