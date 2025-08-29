from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.cleaning_service import clean_data

router = APIRouter()

class CleanRequest(BaseModel):
    file_path: str

@router.post("/clean")
async def clean_endpoint(payload: CleanRequest):
    """
    Endpoint pour nettoyer un fichier CSV/Excel.
    """
    if not payload.file_path:
        raise HTTPException(status_code=400, detail="file_path requis")

    try:
        clean_path = clean_data(payload.file_path)
        return {"clean_path": clean_path}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Fichier introuvable : {payload.file_path}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur interne : {str(e)}")
