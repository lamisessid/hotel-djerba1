from sqlalchemy import Column, Integer, String, Enum, Boolean, Time, TIMESTAMP
from sqlalchemy.sql import func
from database import Base

class HoraireSofra(Base):
    __tablename__ = "horaires_sofra"
    
    id = Column(Integer, primary_key=True, index=True)
    jour_semaine = Column(Enum('lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche'))
    est_ouvert = Column(Boolean, default=False)
    heure_ouverture = Column(Time)
    heure_fermeture = Column(Time)
    created_at = Column(TIMESTAMP, server_default=func.now())