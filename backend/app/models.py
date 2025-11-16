from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime

Base = declarative_base()

class Booking(Base):
    __tablename__ = "bookings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    guest_name = Column(String(100), nullable=False)
    guest_email = Column(String(100), nullable=False)
    guest_phone = Column(String(20), nullable=False)
    check_in = Column(DateTime, nullable=False)
    check_out = Column(DateTime, nullable=False)
    room_type = Column(String(50), nullable=False)
    guests = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(String(20), default="pending")
    special_requests = Column(Text, nullable=True)  
    created_at = Column(DateTime, default=datetime.utcnow)

class RoomType(Base):
    __tablename__ = "room_types"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(Text)
    price_per_night = Column(Float, nullable=False)
    available_rooms = Column(Integer, nullable=False)
    amenities = Column(JSON)
    images = Column(JSON)
    is_active = Column(Boolean, default=True)


class AdminUser(Base):
    __tablename__ = "admin_users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False) 
    is_active = Column(Boolean, default=True)
    role = Column(String(20), default="manager") 
    created_at = Column(DateTime, default=datetime.utcnow)

# === CONFIGURATION DES PRIX ===
class PricingConfig(Base):
    __tablename__ = "pricing_config"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # Suppléments
    single_supplement = Column(Float, default=50.0) 
    pool_view_supplement = Column(Float, default=30.0)  
    # Réductions enfants
    child_discount_2_4 = Column(Float, default=0.3)  
    child_discount_4_12 = Column(Float, default=0.2) 
    # Taxe
    tax_per_night = Column(Float, default=3.0)  
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)