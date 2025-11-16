from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
import database
from services.validation_service import ValidationService
from models.reservation import ReservationMobile, StatutReservation
from services.reservation_service import ReservationService
import json

router = APIRouter()

@router.post("/reserver")
async def creer_reservation(
    chambre: str,
    date_reservation: date,
    heure: str,
    nombre_personnes: int,
    db: Session = Depends(database.get_db)
):
    """Crée une nouvelle réservation"""
    try:
        # Validation préalable
        validation_service = ValidationService(db)
        validation = validation_service.peut_reserver_sofra(chambre, date_reservation, heure)
        
        if not validation["peut_reserver"]:
            raise HTTPException(status_code=400, detail=validation["message"])
        
        # Création de la réservation
        reservation_service = ReservationService(db)
        reservation = reservation_service.creer_reservation(
            chambre=chambre,
            date_reservation=date_reservation,
            heure=heure,
            nombre_personnes=nombre_personnes
        )
        
        return {
            "success": True,
            "message": "Réservation créée avec succès",
            "reservation": {
                "id": reservation.id,
                "chambre": reservation.chambre,
                "date": reservation.date_reservation.isoformat(),
                "heure": reservation.heure,
                "nombre_personnes": reservation.nombre_personnes,
                "statut": reservation.statut.value,
                "qr_code": reservation.qr_code_data
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de réservation: {str(e)}")

@router.get("/reservations/{chambre}")
async def get_reservations_client(
    chambre: str,
    db: Session = Depends(database.get_db)
):
    """Récupère les réservations d'un client"""
    try:
        reservations = db.query(ReservationMobile).filter(
            ReservationMobile.chambre == chambre
        ).order_by(ReservationMobile.date_reservation.desc()).all()
        
        return {
            "success": True,
            "chambre": chambre,
            "reservations": [
                {
                    "id": r.id,
                    "date": r.date_reservation.isoformat(),
                    "heure": r.heure,
                    "nombre_personnes": r.nombre_personnes,
                    "statut": r.statut.value,
                    "created_at": r.created_at.isoformat() if r.created_at else None
                }
                for r in reservations
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de récupération: {str(e)}")