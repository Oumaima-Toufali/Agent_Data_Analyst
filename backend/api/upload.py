# backend/api/upload.py
from fastapi import APIRouter, UploadFile, File, HTTPException
from starlette.responses import JSONResponse
from backend.utils.file_handler import save_upload_file

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Endpoint pour uploader un fichier.
    Stocke le fichier original dans settings.DATA_DIR.
    """
    if not file:
        raise HTTPException(status_code=400, detail="Aucun fichier envoyé")

    try:
        saved_path = await save_upload_file(file)
        return JSONResponse({
            "status": "success",
            "file_path": saved_path
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la sauvegarde du fichier : {str(e)}")
