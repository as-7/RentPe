from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Room(Base):
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String, nullable=False)
    basic_rent_amount = Column(Float, nullable=False)
    water_charge = Column(Float, default=0.0)
    cleaning_charge = Column(Float, default=0.0)
    other_charges = Column(Float, default=0.0)
    is_vacant = Column(Boolean, default=False)
    tenant_name = Column(String, nullable=True)
    tenant_mobile = Column(String, nullable=True)
    
    property_id = Column(Integer, ForeignKey("properties.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    property = relationship("Property", back_populates="rooms")
    leases = relationship("Lease", back_populates="room")
