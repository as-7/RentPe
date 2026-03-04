from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class LeaseBase(BaseModel):
    tenant_id: int
    room_id: int
    deposit_amount: float = 0.0
    start_date: datetime
    end_date: Optional[datetime] = None
    is_active: bool = True

class LeaseCreate(LeaseBase):
    pass

class LeaseUpdate(BaseModel):
    deposit_amount: Optional[float] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None

class LeaseInDBBase(LeaseBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class LeaseResponse(LeaseInDBBase):
    pass
