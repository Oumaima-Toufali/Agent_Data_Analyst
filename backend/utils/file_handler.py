# backend/utils/file_handler.py
import os
from fastapi import UploadFile
from datetime import datetime
from backend.config import settings  # settings.DATA_DIR

# Assurer que le dossier existe
os.makedirs(settings.DATA_DIR, exist_ok=True)

async def save_upload_file(file: UploadFile) -> str:
    """
    Sauvegarde un fichier UploadFile dans DATA_DIR.
    Renomme automatiquement en cas de conflit en ajoutant un timestamp.
    Retourne le chemin complet du fichier sauvegardé.
    """
    filename = file.filename
    base, ext = os.path.splitext(filename)
    
    # Nettoyer le nom de fichier (retirer espaces et caractères spéciaux)
    base = "".join(c for c in base if c.isalnum() or c in ("_", "-")).rstrip()
    ext = ext.lower()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_name = f"{base}_{timestamp}{ext}"
    save_path = os.path.join(settings.DATA_DIR, save_name)

    try:
        contents = await file.read()
        with open(save_path, "wb") as f:
            f.write(contents)
        return save_path
    finally:
        await file.close()
