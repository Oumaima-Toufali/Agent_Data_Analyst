# backend/services/cleaning_service.py
import os
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd

from backend.config import settings

# ----------------- Logging -----------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ----------------- Dossier CLEAN -----------------
CLEAN_DIR = Path(settings.CLEAN_DIR).resolve()
CLEAN_DIR.mkdir(parents=True, exist_ok=True)
logger.info(f"[cleaning_service] Dossier de fichiers nettoyés : {CLEAN_DIR}")

# ----------------- Fonctions -----------------
def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    logger.info(f"[clean_df] Début du nettoyage ({len(df)} lignes, {len(df.columns)} colonnes)")

    df = df.drop_duplicates()
    df = df.replace([float("inf"), float("-inf")], pd.NA)
    empty_cols = df.columns[df.isna().all()].tolist()
    if empty_cols:
        df = df.drop(columns=empty_cols)
        logger.info(f"[clean_df] Colonnes vides supprimées: {empty_cols}")
    df = df.dropna(axis=0, how="all")
    
    for col in df.select_dtypes(include=["object"]).columns:
        if 1 < df[col].nunique(dropna=True) < 50:
            df[col] = df[col].astype("category")
            logger.info(f"[clean_df] Colonne '{col}' convertie en 'category'")
    
    logger.info(f"[clean_df] Nettoyage terminé ({len(df)} lignes, {len(df.columns)} colonnes)")
    return df

def _read_input(file_path: Path, sample_limit: int = 100_000) -> pd.DataFrame:
    suffix = file_path.suffix.lower()
    if suffix in [".xlsx", ".xls"]:
        return pd.read_excel(file_path)
    elif suffix == ".csv":
        return pd.read_csv(file_path)
    else:
        raise ValueError("Format non supporté (CSV/Excel uniquement).")

def _unique_clean_path(original: Path) -> Path:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    candidate = CLEAN_DIR / f"{original.stem}_clean_{ts}{original.suffix}"
    i = 1
    while candidate.exists():
        candidate = CLEAN_DIR / f"{original.stem}_clean_{ts}_{i}{original.suffix}"
        i += 1
    return candidate

def clean_data(file_path: str) -> str:
    p = Path(file_path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Fichier introuvable : {file_path}")

    df = _read_input(p)
    df_cleaned = clean_df(df)
    out_path = _unique_clean_path(p)

    if out_path.suffix.lower() in [".xlsx", ".xls"]:
        df_cleaned.to_excel(out_path, index=False)
    else:
        df_cleaned.to_csv(out_path, index=False)

    logger.info(f"[clean_data] Fichier nettoyé sauvegardé : {out_path}")
    return str(out_path)
