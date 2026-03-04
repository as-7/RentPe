from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class PropertyBase(BaseModel):
    name: str
    address: str
    electricity_per_unit_cost: Optional[float] = 0.0
    water_charge: Optional[float] = 0.0
    cleaning_charge: Optional[float] = 0.0
    other_charges: Optional[float] = 0.0
    billing_due_date: Optional[int] = 1

class PropertyCreate(PropertyBase):
    pass

class RoomGroup(BaseModel):
    count: int
    rent: float
    water: float = 0.0
    cleaning: float = 0.0
    other: float = 0.0
    occupied_count: int = 0

class PropertyBulkCreate(PropertyBase):
    room_groups: List[RoomGroup]

class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    electricity_per_unit_cost: Optional[float] = None
    water_charge: Optional[float] = None
    cleaning_charge: Optional[float] = None
    other_charges: Optional[float] = None
    billing_due_date: Optional[int] = None

class PropertyInDBBase(PropertyBase):
    id: int
    landlord_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

from app.schemas.room import RoomResponse

class PropertyResponse(PropertyInDBBase):
    total_rooms: int = 0
    vacant_rooms: int = 0
    rooms: List[RoomResponse] = []
