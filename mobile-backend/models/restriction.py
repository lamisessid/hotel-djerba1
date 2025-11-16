from sqlalchemy import Column, Integer, String, Date, Boolean, TIMESTAMP, UniqueConstraint
from sqlalchemy.sql import func
from database import Base

class RestrictionSejour(Base):
    __tablename__ = "restrictions_sejour"
    
    id = Column(Integer, primary_key=True, index=True)
    chambre = Column(String(50), nullable=False)
    date_debut_sejour = Column(Date, nullable=False)
    date_fin_sejour = Column(Date, nullable=False)
    a_reserve_sofra = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    __table_args__ = (UniqueConstraint('chambre', 'date_debut_sejour', name='unique_chambre_sejour'),)