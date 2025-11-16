from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
from models.horaire import HoraireSofra
from models.restriction import RestrictionSejour
from models.reservation import ReservationMobile

class ValidationService:
    def __init__(self, db: Session):
        self.db = db
    
    def est_jour_ouvert(self, date_souhaitee: date) -> bool:
        """Vérifie si le restaurant est ouvert ce jour"""
        jour_semaine = date_souhaitee.strftime('%A').lower()
        
        # Conversion pour les noms français
        jours_francais = {
            'monday': 'lundi',
            'tuesday': 'mardi', 
            'wednesday': 'mercredi',
            'thursday': 'jeudi',
            'friday': 'vendredi',
            'saturday': 'samedi',
            'sunday': 'dimanche'
        }
        
        jour_francais = jours_francais.get(jour_semaine, jour_semaine)
        horaire = self.db.query(HoraireSofra).filter(
            HoraireSofra.jour_semaine == jour_francais
        ).first()
        
        return horaire and horaire.est_ouvert
    
    def est_24h_a_l_avance(self, date_souhaitee: date) -> bool:
        """Vérifie la règle des 24h à l'avance"""
        maintenant = datetime.now().date()
        difference = date_souhaitee - maintenant
        return difference.days >= 1
    
    def a_deja_reserve_ce_sejour(self, chambre: str, date_souhaitee: date) -> bool:
        """Vérifie si la chambre a déjà réservé pendant ce séjour"""
        # 1. Vérifier dans les réservations historiques (reservation_elsofra)
        try:
            # Recherche dans reservation_elsofra (données OCR)
            query_historique = text("""
                SELECT COUNT(*) 
                FROM reservation_elsofra 
                WHERE numero_chambre LIKE :chambre 
                AND date_passage = :date
                AND statut = 'confirmé'
            """)
            result_historique = self.db.execute(
                query_historique, 
                {"chambre": f"%{chambre}%", "date": date_souhaitee}
            ).scalar()
            
            historique_trouve = result_historique > 0
        except Exception:
            historique_trouve = False
        
        # 2. Vérifier dans les nouvelles réservations (reservations_mobile)
        reservation_nouvelle = self.db.query(ReservationMobile).filter(
            ReservationMobile.chambre == chambre,
            ReservationMobile.date_reservation == date_souhaitee,
            ReservationMobile.statut.in_(["en_attente", "confirme"])
        ).first()
        
        nouvelle_trouvee = reservation_nouvelle is not None
        
        return historique_trouve or nouvelle_trouvee
    
    def get_heures_disponibles(self, date_souhaitee: date) -> list:
        """Retourne les heures disponibles pour une date"""
        heures_possibles = ["19h30", "20h00"]
        
        # Vérifier la capacité pour chaque heure
        heures_disponibles = []
        for heure in heures_possibles:
            if self._heure_est_disponible(date_souhaitee, heure):
                heures_disponibles.append(heure)
        
        return heures_disponibles
    
    def _heure_est_disponible(self, date_souhaitee: date, heure: str) -> bool:
        """Vérifie si une heure spécifique est disponible"""
        # Compter les réservations existantes pour cette date/heure
        try:
            # Réservations historiques
            query_historique = text("""
                SELECT COUNT(*) 
                FROM reservation_elsofra 
                WHERE date_passage = :date 
                AND heure_passage = :heure
                AND statut = 'confirmé'
            """)
            count_historique = self.db.execute(
                query_historique, 
                {"date": date_souhaitee, "heure": heure}
            ).scalar()
            
            # Réservations nouvelles
            count_nouvelles = self.db.query(ReservationMobile).filter(
                ReservationMobile.date_reservation == date_souhaitee,
                ReservationMobile.heure == heure,
                ReservationMobile.statut.in_(["en_attente", "confirme"])
            ).count()
            
            total_reservations = count_historique + count_nouvelles
            
            # Capacité estimée du restaurant (à ajuster)
            capacite_max = 50  # Exemple
            return total_reservations < capacite_max
            
        except Exception:
            return True  # En cas d'erreur, on suppose disponible
    
    def peut_reserver_sofra(self, chambre: str, date_souhaitee: date, heure: str = None) -> dict:
        """Vérifie toutes les règles métier"""
        validations = {
            "jour_ouvert": self.est_jour_ouvert(date_souhaitee),
            "24h_avance": self.est_24h_a_l_avance(date_souhaitee),
            "premiere_reservation": not self.a_deja_reserve_ce_sejour(chambre, date_souhaitee)
        }
        
        # Vérifier l'heure si fournie
        if heure:
            validations["heure_disponible"] = self._heure_est_disponible(date_souhaitee, heure)
        
        return {
            "peut_reserver": all(validations.values()),
            "validations": validations,
            "heures_disponibles": self.get_heures_disponibles(date_souhaitee),
            "message": self._generer_message_erreur(validations)
        }
    
    def _generer_message_erreur(self, validations: dict) -> str:
        if all(validations.values()):
            return "Réservation possible"
        
        messages = []
        if not validations.get("jour_ouvert", True):
            messages.append("Le restaurant est fermé ce jour")
        if not validations.get("24h_avance", True):
            messages.append("Réservation 24h à l'avance minimum")
        if not validations.get("premiere_reservation", True):
            messages.append("Une réservation par séjour maximum")
        if not validations.get("heure_disponible", True):
            messages.append("Heure non disponible")
        
        return "; ".join(messages) if messages else "Réservation impossible"