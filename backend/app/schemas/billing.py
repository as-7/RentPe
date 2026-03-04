from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class ElectricityReadingBase(BaseModel):
    room_id: int
    reading_units: float
    reading_date: Optional[datetime] = None

class ElectricityReadingCreate(ElectricityReadingBase):
    pass

class ElectricityReadingInDB(ElectricityReadingBase):
    id: int
    
    model_config = ConfigDict(from_attributes=True)

class ElectricityReadingResponse(ElectricityReadingInDB):
    pass


class CustomChargeBase(BaseModel):
    room_id: int
    charge_name: str
    amount: float
    is_recurring: bool = True

class CustomChargeCreate(CustomChargeBase):
    pass

class CustomChargeInDB(CustomChargeBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class CustomChargeResponse(CustomChargeInDB):
    pass


class InvoiceBase(BaseModel):
    tenant_id: int
    room_id: int
    billing_cycle_start: datetime
    billing_cycle_end: datetime
    due_date: datetime
    
    basic_rent: float
    water_charge: float = 0.0
    electricity_charge: float = 0.0
    custom_charges_total: float = 0.0
    total_amount_due: float
    status: str = "pending"

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceInDB(InvoiceBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class InvoiceResponse(InvoiceInDB):
    pass

class RentCalculationPreview(BaseModel):
    room_id: int
    basic_rent: float
    water_charge: float
    electricity_units_consumed: float
    electricity_cost: float
    custom_charges: List[CustomChargeResponse]
    total_due: float
