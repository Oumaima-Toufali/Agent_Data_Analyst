# backend/models/schemas.py
from pydantic import BaseModel

class CleanRequest(BaseModel):
    """
    Requête pour le nettoyage d'un fichier CSV/Excel.
    """
    file_path: str  # chemin vers le fichier original uploadé dans DATA_DIR

class AnalysisRequest(BaseModel):
    """
    Requête pour l'analyse.
    Le champ `clean_file_path` correspond au chemin du fichier nettoyé à analyser.
    """
    question: str
    clean_file_path: str  # chemin vers le fichier nettoyé CSV/Excel dans CLEAN_DIR
