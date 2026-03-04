from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class RoomBase(BaseModel):
    room_number: str
    basic_rent_amount: float
    water_charge: float = 0.0
    is_vacant: bool = True

class RoomCreate(RoomBase):
    property_id: int

class RoomUpdate(BaseModel):
    room_number: Optional[str] = None
    basic_rent_amount: Optional[float] = None
    water_charge: Optional[float] = None
    is_vacant: Optional[bool] = None

class RoomInDBBase(RoomBase):
    id: int
    property_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class RoomResponse(RoomInDBBase):
    pass
