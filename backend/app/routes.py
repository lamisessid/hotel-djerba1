from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, date
from jose import JWTError, jwt
from typing import List
import hashlib
import secrets

from .database import get_db
from .models import Booking, RoomType, AdminUser, PricingConfig
from .config import settings

router = APIRouter()

# ==================== CONFIGURATION SÉCURITÉ ====================

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
security = HTTPBearer()

# ==================== FONCTIONS UTILITAIRES ====================

def hash_password(password: str, salt: str) -> str:
    """Crée un hash SHA256 du mot de passe avec salt"""
    return salt + hashlib.sha256((salt + password).encode()).hexdigest()

def get_password_hash(password: str) -> str:
    """Hash le mot de passe avec salt aléatoire"""
    salt = secrets.token_hex(16)
    return hash_password(password, salt)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie si le mot de passe correspond au hash"""
    if not hashed_password or len(hashed_password) < 32:
        return False
    salt = hashed_password[:32]
    return hash_password(plain_password, salt) == hashed_password

def create_access_token(data: dict) -> str:
    """Crée un JWT token avec expiration"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security), 
    db: Session = Depends(get_db)
) -> AdminUser:
    """Vérifie le token JWT et retourne l'admin connecté"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Token invalide")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")
    
    admin = db.query(AdminUser).filter(AdminUser.username == username).first()
    if not admin or not admin.is_active:
        raise HTTPException(status_code=401, detail="Admin non trouvé ou inactif")
    
    return admin

# ==================== SERVICE DE CALCUL DE PRIX ====================

class PricingService:
    """Service responsable du calcul des prix selon la grille tarifaire"""
    
    @staticmethod
    def calculate_booking_price(
        room_type: RoomType, 
        check_in: date, 
        check_out: date, 
        adults: int, 
        children: List[int], 
        pricing_config: PricingConfig,
        is_single: bool = False, 
        has_pool_view: bool = False
    ) -> dict:
        """
        Calcule le prix total selon la grille tarifaire de l'hôtel
        """
        # Validation des dates
        if check_out <= check_in:
            raise ValueError("La date de départ doit être après la date d'arrivée")
        
        nights = (check_out - check_in).days
        if nights <= 0:
            raise ValueError("Nombre de nuits invalide")

        # Prix de base
        base_price = room_type.price_per_night * adults * nights
        
        # Suppléments
        supplements = 0
        if is_single:
            supplements += pricing_config.single_supplement * nights
        if has_pool_view:
            supplements += pricing_config.pool_view_supplement * nights
        
        # Réductions enfants
        children_discount = 0
        for child_age in children:
            if 2 <= child_age < 4:
                discount_rate = pricing_config.child_discount_2_4
            elif 4 <= child_age < 12:
                discount_rate = pricing_config.child_discount_4_12
            else:
                continue  
            
            children_discount += room_type.price_per_night * discount_rate * nights
        
        # Taxe de séjour
        tax_total = pricing_config.tax_per_night * (adults + len(children)) * nights
        
        # Total final
        total = base_price + supplements - children_discount + tax_total
        
        return {
            "base_price": round(base_price, 2),
            "supplements": round(supplements, 2),
            "children_discount": round(children_discount, 2),
            "tax_total": round(tax_total, 2),
            "total": round(total, 2),
            "nights": nights,
            "price_per_night": room_type.price_per_night
        }

# ==================== ROUTES PUBLIQUES ====================

@router.get("/")
async def root():
    return {"message": "Bienvenue à l'Hôtel Holiday Beach Djerba"}

@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@router.get("/rooms")
async def get_rooms(db: Session = Depends(get_db)):
    rooms = db.query(RoomType).filter(RoomType.is_active == True).all()
    return {"count": len(rooms), "rooms": rooms}

@router.post("/bookings")
async def create_booking(booking_data: dict, db: Session = Depends(get_db)):
    """
    Crée une nouvelle réservation avec calcul automatique du prix
    """
    try:
        # Récupérer configuration
        pricing_config = db.query(PricingConfig).first()
        if not pricing_config:
            raise HTTPException(status_code=500, detail="Configuration des prix manquante")
        
        # Récupérer chambre
        room_type = db.query(RoomType).filter(RoomType.id == booking_data["room_type_id"]).first()
        if not room_type:
            raise HTTPException(status_code=404, detail="Type de chambre non trouvé")
        
        # Validation dates
        check_in = datetime.strptime(booking_data["check_in"], "%Y-%m-%d").date()
        check_out = datetime.strptime(booking_data["check_out"], "%Y-%m-%d").date()
        
        # Calcul prix
        price_details = PricingService.calculate_booking_price(
            room_type=room_type,
            check_in=check_in,
            check_out=check_out,
            adults=booking_data["adults"],
            children=booking_data.get("children", []),
            pricing_config=pricing_config,
            is_single=booking_data.get("is_single", False),
            has_pool_view=booking_data.get("has_pool_view", False)
        )
        
        # Créer réservation
        booking = Booking(
            guest_name=booking_data["guest_name"],
            guest_email=booking_data["guest_email"],
            guest_phone=booking_data["guest_phone"],
            check_in=check_in,
            check_out=check_out,
            room_type=room_type.name,
            guests=booking_data["adults"] + len(booking_data.get("children", [])),
            total_price=price_details["total"],
            status="pending",
            special_requests=booking_data.get("special_requests")
        )
        
        db.add(booking)
        db.commit()
        db.refresh(booking)
        
        return {
            "message": "Réservation créée avec succès",
            "booking_id": booking.id,
            "price_breakdown": price_details,
            "status": "pending"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création: {str(e)}")

# ==================== ROUTES ADMIN ====================

@router.post("/admin/login")
async def admin_login(login_data: dict, db: Session = Depends(get_db)):
    """Authentification admin"""
    username = login_data.get("username")
    password = login_data.get("password")
    
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username et password requis")
    
    admin = db.query(AdminUser).filter(AdminUser.username == username).first()
    if not admin or not verify_password(password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    
    access_token = create_access_token(data={"sub": admin.username})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "admin": {
            "id": admin.id,
            "username": admin.username,
            "email": admin.email,
            "role": admin.role
        }
    }

@router.get("/admin/bookings")
async def get_all_bookings(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Récupère toutes les réservations"""
    bookings = db.query(Booking).order_by(Booking.created_at.desc()).all()
    return {"count": len(bookings), "bookings": bookings}
@router.get("/admin/analytics/advanced")
async def get_advanced_analytics(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Analytics avancées pour le dashboard AI"""
    try:
        bookings = db.query(Booking).all()
        
        if not bookings:
            return {
                "message": "Pas assez de données pour l'analyse",
                "total_bookings": 0,
                "analysis_timestamp": datetime.utcnow().isoformat()
            }
        
        # Tendances mensuelles
        monthly_trends = {}
        for booking in bookings:
            month = booking.created_at.strftime("%Y-%m")
            monthly_trends[month] = monthly_trends.get(month, 0) + 1
        
        # Performance des chambres
        room_performance = {}
        for booking in bookings:
            if booking.room_type not in room_performance:
                room_performance[booking.room_type] = {
                    "total_revenue": 0,
                    "booking_count": 0,
                    "average_rate": 0
                }
            room_performance[booking.room_type]["total_revenue"] += booking.total_price
            room_performance[booking.room_type]["booking_count"] += 1
        
        # Calcul des taux moyens
        for room_type, data in room_performance.items():
            data["average_rate"] = round(data["total_revenue"] / data["booking_count"], 2) if data["booking_count"] > 0 else 0
        
        # Statistiques avancées
        total_revenue = sum(booking.total_price for booking in bookings)
        confirmed_bookings = [b for b in bookings if b.status in ['confirmed', 'checked-in']]
        occupancy_rate = round((len(confirmed_bookings) / len(bookings)) * 100, 2) if bookings else 0
        
        # Chambre la plus populaire
        popular_room = max(room_performance.items(), key=lambda x: x[1]["booking_count"])[0] if room_performance else "N/A"
        
        return {
            "monthly_trends": monthly_trends,
            "room_performance": room_performance,
            "advanced_metrics": {
                "total_revenue": round(total_revenue, 2),
                "occupancy_rate": occupancy_rate,
                "popular_room": popular_room,
                "total_bookings": len(bookings),
                "confirmed_bookings": len(confirmed_bookings)
            },
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'analyse: {str(e)}")

@router.put("/admin/bookings/{booking_id}/status")
async def update_booking_status(
    booking_id: str,
    status_data: dict,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Met à jour le statut d'une réservation"""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Réservation non trouvée")
    
    new_status = status_data.get("status")
    if new_status not in ["pending", "confirmed", "cancelled", "checked-in", "checked-out"]:
        raise HTTPException(status_code=400, detail="Statut invalide")
    
    booking.status = new_status
    db.commit()
    db.refresh(booking)
    
    return {
        "message": f"Statut de la réservation mis à jour vers '{new_status}'",
        "booking_id": booking.id,
        "new_status": booking.status
    }

@router.put("/admin/rooms/{room_id}/price")
async def update_room_price(
    room_id: str, 
    price_data: dict,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Modifie le prix d'une chambre"""
    room = db.query(RoomType).filter(RoomType.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Chambre non trouvée")
    
    new_price = price_data.get("new_price")
    if not new_price or new_price <= 0:
        raise HTTPException(status_code=400, detail="Prix invalide")
    
    room.price_per_night = new_price
    db.commit()
    
    return {
        "message": "Prix mis à jour avec succès",
        "room_id": room.id,
        "room_name": room.name,
        "new_price": room.price_per_night
    }

@router.put("/admin/pricing-config")
async def update_pricing_config(
    config_data: dict, 
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Modifie la configuration des prix"""
    pricing_config = db.query(PricingConfig).first() or PricingConfig()
    if not db.query(PricingConfig).first():
        db.add(pricing_config)
    
    updated_fields = []
    for key, value in config_data.items():
        if hasattr(pricing_config, key) and value is not None:
            setattr(pricing_config, key, value)
            updated_fields.append(key)
    
    db.commit()
    
    return {
        "message": "Configuration des prix mise à jour",
        "updated_fields": updated_fields
    }

@router.get("/admin/dashboard")
async def get_dashboard(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Dashboard admin avec statistiques"""
    total_bookings = db.query(Booking).count()
    total_revenue = db.query(func.sum(Booking.total_price)).scalar() or 0
    pending_bookings = db.query(Booking).filter(Booking.status == "pending").count()
    confirmed_bookings = db.query(Booking).filter(Booking.status == "confirmed").count()
    
    # Revenu du mois en cours
    current_month = datetime.utcnow().month
    current_year = datetime.utcnow().year
    monthly_revenue = db.query(func.sum(Booking.total_price)).filter(
        func.extract('month', Booking.created_at) == current_month,
        func.extract('year', Booking.created_at) == current_year
    ).scalar() or 0
    
    return {
        "overview": {
            "total_bookings": total_bookings,
            "total_revenue": round(total_revenue, 2),
            "monthly_revenue": round(monthly_revenue, 2),
            "pending_bookings": pending_bookings,
            "confirmed_bookings": confirmed_bookings
        },
        "timestamp": datetime.utcnow().isoformat()
    }

# ==================== INITIALISATION ====================

@router.post("/setup")
async def setup_database(db: Session = Depends(get_db)):
    """Initialise la base de données"""
    if db.query(AdminUser).first():
        return {"message": "Base de données déjà initialisée"}
    
    # Admin
    admin = AdminUser(
        username=settings.ADMIN_USERNAME,
        email=settings.ADMIN_EMAIL, 
        hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
        role="admin"
    )
    db.add(admin)
    
    # Configuration prix
    pricing_config = PricingConfig(
        single_supplement=settings.SINGLE_SUPPLEMENT,
        pool_view_supplement=settings.POOL_VIEW_SUPPLEMENT,
        child_discount_2_4=settings.CHILD_DISCOUNT_2_4,
        child_discount_4_12=settings.CHILD_DISCOUNT_4_12,
        tax_per_night=settings.TAX_PER_NIGHT
    )
    db.add(pricing_config)
    
    # Chambres
    rooms = [
        RoomType(
            name="Double Standard Vue Jardin", 
            description="Chambre confortable avec vue sur le jardin", 
            price_per_night=120.0, 
            available_rooms=10,
            amenities=["WiFi", "AC", "TV", "Coffre-fort"]
        ),
        RoomType(
            name="Double Supérieure Vue Piscine", 
            description="Chambre spacieuse avec vue directe sur la piscine", 
            price_per_night=150.0, 
            available_rooms=5,
            amenities=["WiFi", "AC", "TV", "Coffre-fort", "Mini-bar", "Terrasse"]
        ),
    ]
    db.add_all(rooms)
    
    db.commit()
    
    return {
        "message": "Base de données initialisée avec succès",
        "admin_created": {"username": settings.ADMIN_USERNAME, "email": settings.ADMIN_EMAIL},
        "note": "Changez le mot de passe admin en production!"
    }