from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, func, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base

class ElectricityReading(Base):
    __tablename__ = "electricity_readings"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), index=True, nullable=False)
    reading_date = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    reading_units = Column(Float, nullable=False)
    
    # Relationships
    room = relationship("Room")


class CustomCharge(Base):
    __tablename__ = "custom_charges"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), index=True, nullable=False)
    charge_name = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    is_recurring = Column(Boolean, default=True) # Applies to every monthly invoice
    
    # Relationships
    room = relationship("Room")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), index=True, nullable=False)
    
    billing_cycle_start = Column(DateTime(timezone=True), nullable=False)
    billing_cycle_end = Column(DateTime(timezone=True), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=False)
    
    # Breakdown lines
    basic_rent = Column(Float, nullable=False)
    water_charge = Column(Float, default=0.0)
    cleaning_charge = Column(Float, default=0.0)
    other_charges = Column(Float, default=0.0)
    electricity_charge = Column(Float, default=0.0)
    custom_charges_total = Column(Float, default=0.0)
    
    total_amount_due = Column(Float, nullable=False)
    
    status = Column(String, default="pending") # "pending", "paid", "overdue"
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tenant = relationship("User")
    room = relationship("Room")


class ReminderLog(Base):
    __tablename__ = "reminder_logs"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), index=True, nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), index=True, nullable=False)
    target_due_date = Column(Date, nullable=False, index=True)
    days_before_due = Column(Integer, nullable=False)
    tenant_mobile = Column(String, nullable=False)
    status = Column(String, default="sent", nullable=False)
    provider_message_id = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    property = relationship("Property")
    room = relationship("Room")
