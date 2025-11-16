from sqlalchemy.orm import Session
from models.reservation import ReservationMobile, StatutReservation
from models.restriction import RestrictionSejour
from datetime import timedelta
import qrcode
import json

class ReservationService:
    def __init__(self, db: Session):
        self.db = db
    
    def creer_reservation(self, chambre: str, date_reservation, heure: str, nombre_personnes: int):
        """Crée une nouvelle réservation avec QR code"""
        
        # Créer la réservation
        reservation = ReservationMobile(
            chambre=chambre,
            date_reservation=date_reservation,
            heure=heure,
            nombre_personnes=nombre_personnes,
            statut=StatutReservation.en_attente
        )
        
        # Générer le QR code
        qr_data = self._generer_qr_data(reservation)
        reservation.qr_code_data = self._generer_qr_code(qr_data)
        
        # Sauvegarder
        self.db.add(reservation)
        self.db.commit()
        self.db.refresh(reservation)
        
        # Marquer la restriction de séjour
        self._creer_restriction_sejour(chambre, date_reservation)
        
        return reservation
    
    def _generer_qr_data(self, reservation):
        """Génère les données pour le QR code"""
        return {
            "reservation_id": reservation.id,
            "chambre": reservation.chambre,
            "date": reservation.date_reservation.isoformat(),
            "heure": reservation.heure,
            "nombre_personnes": reservation.nombre_personnes,
            "restaurant": "El Sofra"
        }
    
    def _generer_qr_code(self, data):
        """Génère un QR code à partir des données"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(json.dumps(data))
            qr.make(fit=True)
            
          
            return json.dumps(data)
            
        except Exception:
            # Fallback: retourner les données sans QR code
            return json.dumps(data)
    
    def _creer_restriction_sejour(self, chambre: str, date_reservation):
        """Crée une entrée de restriction pour le séjour"""
        debut_sejour = date_reservation - timedelta(days=3)
        fin_sejour = date_reservation + timedelta(days=3)
        
        restriction = RestrictionSejour(
            chambre=chambre,
            date_debut_sejour=debut_sejour,
            date_fin_sejour=fin_sejour,
            a_reserve_sofra=True
        )
        
        self.db.add(restriction)
        self.db.commit()