from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class PropertyBase(BaseModel):
    name: str
    address: str
    electricity_per_unit_cost: float = 0.0

class PropertyCreate(PropertyBase):
    pass

class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    electricity_per_unit_cost: Optional[float] = None

class PropertyInDBBase(PropertyBase):
    id: int
    landlord_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class PropertyResponse(PropertyInDBBase):
    pass
