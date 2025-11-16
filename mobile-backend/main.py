from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime  
import database
from routes import reservations, disponibilite, admin

app = FastAPI(title="El Sofra Mobile API", version="1.0.0")

# CORS pour l'app mobile
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routes
app.include_router(reservations.router, prefix="/api/mobile", tags=["reservations"])
app.include_router(disponibilite.router, prefix="/api/mobile", tags=["disponibilite"])
app.include_router(admin.router, prefix="/api/mobile/admin", tags=["admin"])

@app.get("/")
async def root():
    return {"message": "El Sofra Mobile API - Prêt pour les réservations"}

@app.get("/health")
async def health_check(db: Session = Depends(database.get_db)):
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}  

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)