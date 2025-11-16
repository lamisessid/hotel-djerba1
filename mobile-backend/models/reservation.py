from sqlalchemy import Column, Integer, String, Date, Boolean, Enum, Text, TIMESTAMP
from sqlalchemy.sql import func
from database import Base
import enum

class StatutReservation(enum.Enum):
    en_attente = "en_attente"
    confirme = "confirme"
    annule = "annule"

class ReservationMobile(Base):
    __tablename__ = "reservations_mobile"
    
    id = Column(Integer, primary_key=True, index=True)
    chambre = Column(String(50), nullable=False)
    date_reservation = Column(Date, nullable=False)
    heure = Column(String(10), nullable=False)  
    nombre_personnes = Column(Integer, nullable=False)
    statut = Column(Enum(StatutReservation), default=StatutReservation.en_attente)
    qr_code_data = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())