from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date
import database
from services.validation_service import ValidationService

router = APIRouter()

@router.get("/disponibilite/{chambre}/{date_souhaitee}")
async def verifier_disponibilite(
    chambre: str,
    date_souhaitee: date,
    db: Session = Depends(database.get_db)
):
    """Vérifie si une réservation est possible"""
    try:
        validation_service = ValidationService(db)
        resultat = validation_service.peut_reserver_sofra(chambre, date_souhaitee)
        
        return {
            "success": True,
            "data": resultat,
            "chambre": chambre,
            "date_souhaitee": date_souhaitee.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de vérification: {str(e)}")

@router.get("/heures-disponibles/{date_souhaitee}")
async def get_heures_disponibles(
    date_souhaitee: date,
    db: Session = Depends(database.get_db)
):
    """Retourne les heures disponibles pour une date"""
    try:
        validation_service = ValidationService(db)
        heures = validation_service.get_heures_disponibles(date_souhaitee)
        
        return {
            "success": True,
            "date": date_souhaitee.isoformat(),
            "heures_disponibles": heures
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de récupération: {str(e)}")