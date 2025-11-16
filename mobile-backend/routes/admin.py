from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
import secrets
import database
from models.reservation import ReservationMobile, StatutReservation
from models.admin import AdminUser

router = APIRouter()
security = HTTPBasic()

def verify_password(plain_password, hashed_password):
    return secrets.compare_digest(plain_password, hashed_password)

def authenticate_admin(credentials: HTTPBasicCredentials = Depends(security), db: Session = Depends(database.get_db)):
    admin_user = db.query(AdminUser).filter(
        AdminUser.username == credentials.username,
        AdminUser.is_active == True
    ).first()
    
    if not admin_user:
        raise HTTPException(
            status_code=401,
            detail="Identifiants incorrects",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    if not verify_password(credentials.password, admin_user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Identifiants incorrects",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return credentials.username

@router.post("/login")
async def admin_login(admin: str = Depends(authenticate_admin)):
    return {
        "success": True,
        "message": "Connexion réussie",
        "admin": {
            "username": admin
        }
    }

@router.get("/reservations")
async def get_reservations_admin(
    date_filter: date = None,
    statut: str = None,
    db: Session = Depends(database.get_db),
    admin: str = Depends(authenticate_admin)
):
    try:
        query = db.query(ReservationMobile)
        
        if date_filter:
            query = query.filter(ReservationMobile.date_reservation == date_filter)
        
        if statut:
            query = query.filter(ReservationMobile.statut == StatutReservation(statut))
        
        reservations = query.order_by(ReservationMobile.date_reservation.desc()).all()
        
        return {
            "success": True,
            "count": len(reservations),
            "reservations": [
                {
                    "id": r.id,
                    "chambre": r.chambre,
                    "date": r.date_reservation.isoformat(),
                    "heure": r.heure,
                    "nombre_personnes": r.nombre_personnes,
                    "statut": r.statut.value,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "qr_code": r.qr_code_data is not None
                }
                for r in reservations
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de récupération: {str(e)}")

@router.patch("/reservations/{reservation_id}/statut")
async def update_statut_reservation(
    reservation_id: int,
    nouveau_statut: str,
    db: Session = Depends(database.get_db),
    admin: str = Depends(authenticate_admin)
):
    try:
        reservation = db.query(ReservationMobile).filter(
            ReservationMobile.id == reservation_id
        ).first()
        
        if not reservation:
            raise HTTPException(status_code=404, detail="Réservation non trouvée")
        
        reservation.statut = StatutReservation(nouveau_statut)
        reservation.updated_at = datetime.now()
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Statut mis à jour: {nouveau_statut}",
            "reservation": {
                "id": reservation.id,
                "statut": reservation.statut.value
            }
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Statut invalide")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur de mise à jour: {str(e)}")

@router.get("/stats")
async def get_admin_stats(
    db: Session = Depends(database.get_db),
    admin: str = Depends(authenticate_admin) 
):
    try:
        aujourdhui = datetime.now().date()
        demain = aujourdhui + timedelta(days=1)
        
        print(f"=== DEBUG STATS ===")
        print(f"Date aujourd'hui: {aujourdhui}")
        print(f"Date demain: {demain}")
        
        # Récupérer les réservations à partir de demain
        reservations_futures = db.query(ReservationMobile).filter(
            ReservationMobile.date_reservation >= demain
        ).all()
        
        print(f"Nombre de réservations futures trouvées: {len(reservations_futures)}")
        
        # Afficher chaque réservation trouvée
        for r in reservations_futures:
            print(f"Reservation {r.id}: chambre {r.chambre}, date {r.date_reservation}, statut {r.statut.value}")
        
        total_futures = len(reservations_futures)
        en_attente = len([r for r in reservations_futures if r.statut == StatutReservation.en_attente])
        confirmees = len([r for r in reservations_futures if r.statut == StatutReservation.confirme])
        annulees = len([r for r in reservations_futures if r.statut == StatutReservation.annule])
        
        print(f"Stats - Total: {total_futures}, En attente: {en_attente}, Confirmées: {confirmees}, Annulées: {annulees}")
        print(f"=== FIN DEBUG ===")
        
        return {
            "success": True,
            "stats": {
                "total_aujourdhui": total_futures,
                "en_attente": en_attente,
                "confirmees": confirmees,
                "annulees": annulees
            },
            "reservations_aujourdhui": [
                {
                    "id": r.id,
                    "chambre": r.chambre,
                    "date": r.date_reservation.isoformat(),
                    "heure": r.heure,
                    "nombre_personnes": r.nombre_personnes,
                    "statut": r.statut.value
                }
                for r in reservations_futures
            ]
        }
    except Exception as e:
        print(f"ERREUR dans get_admin_stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur de récupération des stats: {str(e)}")

@router.get("/debug/all-reservations")
async def debug_all_reservations(
    db: Session = Depends(database.get_db),
    admin: str = Depends(authenticate_admin)
):
    """Endpoint de debug pour voir toutes les réservations"""
    try:
        toutes_reservations = db.query(ReservationMobile).order_by(ReservationMobile.date_reservation.desc()).all()
        
        print(f"DEBUG: {len(toutes_reservations)} réservations trouvées en base")
        
        return {
            "success": True,
            "count": len(toutes_reservations),
            "reservations": [
                {
                    "id": r.id,
                    "chambre": r.chambre,
                    "date": r.date_reservation.isoformat(),
                    "heure": r.heure,
                    "nombre_personnes": r.nombre_personnes,
                    "statut": r.statut.value,
                    "created_at": r.created_at.isoformat() if r.created_at else None
                }
                for r in toutes_reservations
            ]
        }
    except Exception as e:
        print(f"DEBUG ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur debug: {str(e)}")