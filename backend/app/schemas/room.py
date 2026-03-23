from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class RoomBase(BaseModel):
    room_number: str
    basic_rent_amount: Optional[float] = 0.0
    water_charge: Optional[float] = 0.0
    cleaning_charge: Optional[float] = 0.0
    other_charges: Optional[float] = 0.0
    is_vacant: bool = False
    tenant_name: Optional[str] = None
    tenant_mobile: Optional[str] = None

class RoomCreate(RoomBase):
    property_id: int

class RoomUpdate(BaseModel):
    room_number: Optional[str] = None
    basic_rent_amount: Optional[float] = None
    water_charge: Optional[float] = None
    cleaning_charge: Optional[float] = None
    other_charges: Optional[float] = None
    is_vacant: Optional[bool] = None
    tenant_name: Optional[str] = None
    tenant_mobile: Optional[str] = None
    last_reading: Optional[float] = None # For quick entry initialization

class RoomInDBBase(RoomBase):
    id: int
    property_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class RoomResponse(RoomInDBBase):
    current_electricity_cost: float = 0.0
    current_reading: Optional[float] = None
    last_reading: Optional[float] = None
    last_units_consumed: float = 0.0
    total_monthly_rent: float = 0.0
