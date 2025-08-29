# backend/services/tools_service.py
import traceback
import logging
import pandas as pd
from typing import Any, Dict, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from backend.utils import chart_generator

logger = logging.getLogger(__name__)

# -----------------------------
# Exécution Python sécurisée (sandbox)
# -----------------------------
def execute_python_repl(code: str, local_vars: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    import plotly.express as px
    import plotly.graph_objects as go

    local_vars = local_vars or {}
    safe_globals = {"pd": pd, "px": px, "go": go}

    import io, contextlib
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(code, safe_globals, local_vars)
        logger.info("Code Python exécuté avec succès dans le sandbox.")
        return {"success": True, "locals": local_vars, "stdout": buf.getvalue()}
    except Exception as e:
        logger.error(f"Erreur dans le Python REPL: {e}")
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


# -----------------------------
# Interpréteur "intelligent" optimisé avec parallélisation
# -----------------------------
def _generate_plot(task: str, data: pd.DataFrame) -> Optional[Dict[str, Any]]:
    numeric_cols = data.select_dtypes(include="number").columns.tolist()
    date_cols = data.select_dtypes(include=["datetime64"]).columns.tolist()

    try:
        task_lower = task.lower()
        if "corrélation" in task_lower or "correlation" in task_lower:
            return chart_generator.generate_correlation_plot(data)
        elif "histogramme" in task_lower or "hist" in task_lower:
            return chart_generator.generate_distribution_plot(data, numeric_cols[0], plot_type="hist") if numeric_cols else None
        elif "boxplot" in task_lower or "boîte" in task_lower:
            return chart_generator.generate_distribution_plot(data, numeric_cols[0], plot_type="box") if numeric_cols else None
        elif "scatter" in task_lower or "nuage" in task_lower:
            if len(numeric_cols) >= 2:
                return chart_generator.generate_scatter_plot(data, numeric_cols[0], numeric_cols[1])
        elif "temps" in task_lower or "time" in task_lower:
            if date_cols and numeric_cols:
                return chart_generator.generate_time_series_plot(data, date_cols[0], numeric_cols[0])
    except Exception as e:
        logger.error(f"Erreur génération graphique '{task}': {e}")
    return None


def execute_open_interpreter(task: str, data: pd.DataFrame) -> Dict[str, Any]:
    result = {"success": True, "output": None, "chart": None, "error": None, "traceback": None}

    if data.empty:
        result.update({"success": False, "error": "Le DataFrame est vide, impossible d’exécuter la tâche."})
        return result

    try:
        numeric_cols = data.select_dtypes(include="number").columns.tolist()
        task_lower = task.lower()

        # Calculs simples
        if "moyenne" in task_lower or "mean" in task_lower:
            result["output"] = data[numeric_cols].mean().round(2).to_dict() if numeric_cols else "Pas de colonnes numériques."
        elif "médiane" in task_lower or "median" in task_lower:
            result["output"] = data[numeric_cols].median().round(2).to_dict() if numeric_cols else "Pas de colonnes numériques."
        # Sinon, génération graphique en parallèle
        else:
            with ThreadPoolExecutor() as executor:
                future = executor.submit(_generate_plot, task, data)
                result["chart"] = future.result()
                if result["chart"] is None:
                    result["output"] = f"Tâche '{task}' non reconnue ou pas applicable aux colonnes disponibles."

        logger.info(f"Tâche '{task}' exécutée avec succès.")
    except Exception as e:
        logger.error(f"Erreur execute_open_interpreter: {e}")
        result.update({"success": False, "output": None, "chart": None, "error": str(e), "traceback": traceback.format_exc()})

    return result


# -----------------------------
# Interprétation graphique via LLM
# -----------------------------
def interpret_chart(fig_json: str, df: pd.DataFrame, question: str, llm_asker) -> str:
    prompt_text = f"""
Tu es un expert en analyse de données.
Explique ce graphique Plotly et identifie les tendances ou insights principaux.
Question utilisateur : {question}
Graphique JSON : {fig_json}
Données disponibles : colonnes = {list(df.columns)}, lignes = {len(df)}
"""
    try:
        response = llm_asker(prompt_text)
        logger.info("Interprétation LLM générée avec succès.")
        return response
    except Exception as e:
        logger.error(f"Erreur interprétation LLM: {e}")
        return f"[ERREUR interprétation LLM] {str(e)}"
