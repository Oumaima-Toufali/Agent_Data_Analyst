# backend/main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import upload, clean, analyze
from backend.config import settings

# ==================== INITIALISATION DES DOSSIERS ====================
os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(settings.CLEAN_DIR, exist_ok=True)
os.makedirs("backend/reports", exist_ok=True)  # dossier pour rapports HTML/PDF

# ==================== APPLICATION FASTAPI ====================
app = FastAPI(
    title="AI Data Analyst Agent API",
    description="API pour un agent IA capable d'analyser tout type de dataset tabulaire",
    version="1.0.0"
)

# ==================== CORS ====================
# 🔹 Autoriser toutes les origines pour dev, à restreindre en prod
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # changer pour prod, ex: ["https://monfrontend.com"]
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== ROUTES ====================
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(clean.router, prefix="/api", tags=["Cleaning"])
app.include_router(analyze.router, prefix="/api", tags=["Analysis"])  

# ==================== ENDPOINT DE SANTÉ ====================
@app.get("/", tags=["Health"])
def health():
    """
    Vérifie que le service fonctionne.
    """
    return {"status": "ok", "service": "AI Data Analyst Agent API"}

# ==================== STARTUP/SHUTDOWN EVENTS ====================
@app.on_event("startup")
async def startup_event():
    # Ici tu peux initialiser des connexions LLM, logs, cache, etc.
    print("✅ AI Data Analyst Agent API démarrée")

@app.on_event("shutdown")
async def shutdown_event():
    # Fermer connexions, nettoyer ressources si besoin
    print("🛑 AI Data Analyst Agent API arrêtée")
