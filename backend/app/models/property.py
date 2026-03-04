from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    address = Column(String, nullable=False)
    electricity_per_unit_cost = Column(Float, default=0.0) 
    water_charge = Column(Float, default=0.0)
    cleaning_charge = Column(Float, default=0.0)
    other_charges = Column(Float, default=0.0)
    billing_due_date = Column(Integer, default=1) # Day of month (1-31)
    
    landlord_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    landlord = relationship("User", back_populates="properties")
    rooms = relationship("Room", back_populates="property", cascade="all, delete-orphan")
