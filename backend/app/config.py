import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class Settings:
    # ==================== SÉCURITÉ ====================
    SECRET_KEY: str = os.getenv("SECRET_KEY", "Key_Secure789!")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    
    # ==================== BASE DE DONNÉES ====================
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./hotel.db")
    
    # ==================== ADMIN PAR DÉFAUT ====================
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@hotel.com")
    
    # ==================== CONFIGURATION HÔTEL ====================
    HOTEL_NAME: str = os.getenv("HOTEL_NAME", "Holiday Beach Djerba")
    HOTEL_EMAIL: str = os.getenv("HOTEL_EMAIL", "booking@holidaybeach.com.tn")
    HOTEL_PHONE: str = os.getenv("HOTEL_PHONE", "+216 75 758 063")
    HOTEL_ADDRESS: str = os.getenv("HOTEL_ADDRESS", "Plage Sidi Mehrez BP 90 Djerba - Tunisia, Djerba, Tunisia")
    
    # ==================== CONFIGURATION PRIX ====================
    SINGLE_SUPPLEMENT: float = float(os.getenv("SINGLE_SUPPLEMENT", "50.0"))
    POOL_VIEW_SUPPLEMENT: float = float(os.getenv("POOL_VIEW_SUPPLEMENT", "30.0"))
    CHILD_DISCOUNT_2_4: float = float(os.getenv("CHILD_DISCOUNT_2_4", "0.3"))
    CHILD_DISCOUNT_4_12: float = float(os.getenv("CHILD_DISCOUNT_4_12", "0.2"))
    TAX_PER_NIGHT: float = float(os.getenv("TAX_PER_NIGHT", "3.0"))

# Instance globale des paramètres
settings = Settings()