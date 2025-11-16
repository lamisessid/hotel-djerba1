from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routes import router
from .config import settings
from .models import *

# Créer les tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.HOTEL_NAME,  
    version="1.0.0",
    description=f"API de réservation pour {settings.HOTEL_NAME}",
    contact={
        "name": "Support",
        "email": settings.HOTEL_EMAIL,
        "phone": settings.HOTEL_PHONE
    }
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(router)

@app.get("/")
async def root():
    return {
        "message": f"Bienvenue à l'{settings.HOTEL_NAME}",
        "hotel": {
            "name": settings.HOTEL_NAME,
            "email": settings.HOTEL_EMAIL,
            "phone": settings.HOTEL_PHONE,
            "address": settings.HOTEL_ADDRESS
        },
        "api_version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": settings.HOTEL_NAME,
        "timestamp": datetime.utcnow().isoformat()
    }