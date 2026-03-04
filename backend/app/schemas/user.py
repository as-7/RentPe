from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    phone_number: str
    full_name: Optional[str] = None
    role: str = "tenant"

class UserCreate(UserBase):
    # Depending on auth flow (e.g. Firebase), password might not be needed.
    # Currently assuming OTP purely validates phone.
    pass

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

class UserInDB(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserResponse(UserInDB):
    pass
