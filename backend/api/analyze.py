# backend/api/analyze.py
import os
import base64
import logging
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException

from backend.services.llm_service import smart_agent
from backend.services.report_service import generate_report
from backend.services.cleaning_service import clean_df
from backend.models.schemas import AnalysisRequest
from backend.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

REPORT_DIR = "backend/reports"
os.makedirs(REPORT_DIR, exist_ok=True)

MAX_ROWS = 10000
MAX_COLS = 30
REPORT_RETENTION_DAYS = 3

def cleanup_old_reports(directory: str, days: int = REPORT_RETENTION_DAYS):
    now = datetime.now()
    cutoff = now - timedelta(days=days)
    for filename in os.listdir(directory):
        if not filename.endswith((".html", ".pdf")):
            continue
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            if file_time < cutoff:
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.warning(f"Impossible de supprimer {filename} : {e}")

def encode_file_base64(path: str) -> str:
    if not path or not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def validate_clean_file(file_path: str) -> Path:
    p = Path(file_path).resolve()
    clean_dir = Path(settings.CLEAN_DIR).resolve()
    try:
        p.relative_to(clean_dir)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Le fichier doit se trouver dans le dossier nettoyé : {clean_dir}"
        )
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"Fichier nettoyé introuvable : {p}")
    return p

def read_input(file_path: Path) -> pd.DataFrame:
    if file_path.suffix.lower() == ".csv":
        return pd.read_csv(file_path)
    elif file_path.suffix.lower() in [".xls", ".xlsx"]:
        return pd.read_excel(file_path)
    else:
        raise HTTPException(status_code=400, detail="Format de fichier non supporté")

@router.post("/analyze")
async def analyze_endpoint(req: AnalysisRequest):
    try:
        cleanup_old_reports(REPORT_DIR)

        clean_file = validate_clean_file(req.clean_file_path)
        df = read_input(clean_file)
        logger.info(f"Analyse lancée sur fichier nettoyé : {clean_file}, shape={df.shape}")

        # Nettoyage minimal
        df = clean_df(df)
        logger.info(f"DataFrame après nettoyage minimal : shape={df.shape}, colonnes={list(df.columns)}")

        # Échantillonnage et limitation des colonnes
        if len(df) > MAX_ROWS:
            df = df.sample(MAX_ROWS, random_state=42)
            logger.info(f"Dataset échantillonné à {MAX_ROWS} lignes")
        if df.shape[1] > MAX_COLS:
            df = df.iloc[:, :MAX_COLS]
            logger.info(f"Dataset limité à {MAX_COLS} colonnes")

        # Conversion intelligente pour LLM
        for col in df.select_dtypes(include="object").columns:
            df[col] = df[col].fillna("N/A") if df[col].nunique() < 50 else df[col].astype(str).fillna("")
        for col in df.select_dtypes(include="datetime").columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

        # Appel de l'agent IA
        analysis_results = smart_agent(df, req.question)
        if "error" in analysis_results:
            raise HTTPException(status_code=400, detail=analysis_results["error"])

        # Charts
        chart_jsons = [c.get("fig_json") for c in analysis_results.get("charts", []) if c.get("fig_json")]

        # Génération du rapport
        report = generate_report(
            question=req.question,
            response=analysis_results,
            df=df,
            chart_jsons=chart_jsons,
            stats=analysis_results.get("stats", {}),
            summary_interpretation=analysis_results.get("llm", ""),
            recommendations=analysis_results.get("insights", "")
        )

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        html_path = os.path.join(REPORT_DIR, f"report_{timestamp}.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(report["html_content"])

        pdf_path = report.get("pdf")
        html_b64 = encode_file_base64(html_path)
        pdf_b64 = encode_file_base64(pdf_path)

        logger.info(f"Analyse terminée avec succès: HTML + PDF générés")

        return {
            "status": "success",
            "analysis": {
                "summary": analysis_results.get("llm", ""),
                "recommendations": analysis_results.get("insights", ""),
                "stats": analysis_results.get("stats", {}),
                "charts": chart_jsons
            },
            "report_html": html_b64,
            "report_pdf": pdf_b64
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Erreur pendant l'analyse")
        raise HTTPException(status_code=500, detail=str(e))
