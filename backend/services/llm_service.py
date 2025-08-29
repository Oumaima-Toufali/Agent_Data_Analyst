# backend/services/llm_service.py
import json
import logging
import os
from typing import Dict, Any, List
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from backend.services.eda_service import IntelligentEDAService
from backend.services import tools_service
from backend.utils.chart_generator import (
    generate_correlation_plot,
    generate_distribution_plot,
    generate_time_series_plot
)
from backend.utils.chat_logger import log_interaction

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- CONFIG LLM ---
GITHUB_ENDPOINT = os.environ.get("GITHUB_ENDPOINT", "https://models.github.ai/inference")
GITHUB_MODEL = os.environ.get("GITHUB_MODEL", "gpt-4.1")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("⚠️ GITHUB_TOKEN non défini.")

client = ChatCompletionsClient(endpoint=GITHUB_ENDPOINT, credential=AzureKeyCredential(GITHUB_TOKEN))

ANALYST_PROMPT = """
Tu es un expert Data Analyst IA. Analyse uniquement les données réelles fournies.
Ne jamais générer de code ni inventer des données.
Fournis des explications claires, synthétiques et structurées adaptées au type de données.
"""

INSIGHT_PROMPT = """
Tu es un expert en data analysis avancée.
Utilise uniquement les informations statistiques fournies.
Génère un TOP 5 des insights clés et recommandations exploitables.
"""

# --- FONCTIONS LLM ---
def ask_llm(prompt: str, system_prompt: str = ANALYST_PROMPT, retries: int = 3, delay: float = 1.0) -> str:
    """Appel LLM robuste avec retries pour réduire risque de timeout / déconnexion."""
    for attempt in range(retries):
        try:
            resp = client.complete(
                model=GITHUB_MODEL,
                messages=[SystemMessage(content=system_prompt), UserMessage(content=prompt)],
                temperature=0.3,
                top_p=1.0
            )
            if resp and resp.choices:
                return (resp.choices[0].message.content or "").strip()
            else:
                logger.warning(f"LLM returned empty response, attempt {attempt+1}")
        except Exception as e:
            logger.error(f"Erreur LLM attempt {attempt+1}: {e}")
        time.sleep(delay)
    return "❌ Erreur LLM après plusieurs tentatives."

# --- STATISTIQUES DESCRIPTIVES ---
def robust_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Stats résumées pour gros datasets, compatible LLM."""
    types = {
        "numeric": df.select_dtypes(include="number").columns.tolist(),
        "datetime": df.select_dtypes(include=["datetime64[ns]"]).columns.tolist(),
        "categorical": df.select_dtypes(include=["object", "category"]).columns.tolist()
    }
    stats = {"rows": len(df), "columns": list(df.columns), "dtypes": {c: str(df[c].dtype) for c in df.columns}}
    
    if types["numeric"]:
        stats["numeric"] = df[types["numeric"]].describe(percentiles=[0.25,0.5,0.75]).to_dict()
    if types["datetime"]:
        stats["datetime"] = {c: {"min": str(df[c].min()), "max": str(df[c].max()), "nunique": int(df[c].nunique())} 
                             for c in types["datetime"] if not df[c].dropna().empty}
    if types["categorical"]:
        stats["categorical"] = {c: df[c].value_counts(dropna=False).head(10).to_dict() for c in types["categorical"]}
    
    return stats

def generate_insights(df: pd.DataFrame, stats: Dict[str, Any], question: str) -> str:
    """Résumé compact + LLM pour éviter prompts trop longs."""
    sample_values = df.head(5).to_dict(orient="records")
    prompt_text = f"""
Question: {question}
Stats: {json.dumps(stats, indent=2)}
Colonnes: {list(df.columns)}
Exemple de valeurs (5 lignes): {json.dumps(sample_values, indent=2)}
"""
    return ask_llm(prompt_text, INSIGHT_PROMPT)

def needs_tools(question: str) -> Dict[str, bool]:
    """Détecte si question nécessite plots ou REPL."""
    q = (question or "").lower()
    repl_triggers = ["moyenne", "écart-type", "variance", "corrélation", "statistique", "résumé"]
    plot_triggers = ["graphique", "plot", "visualisation", "nuage de points", "courbe", "diagramme", 
                     "heatmap", "barres", "boxplot", "line chart", "scatter", "tendance", "série temporelle"]
    return {"repl": any(w in q for w in repl_triggers), "plot": any(w in q for w in plot_triggers)}

# --- AGENT IA INTELLIGENT ---
def smart_agent(df: pd.DataFrame, question: str) -> Dict[str, Any]:
    if df.empty:
        return {"error": "DataFrame vide, impossible d’analyser"}

    out = {"used": [], "messages": [], "eda_reports": {}, "repl": {}, "charts": [],
           "llm": "", "insights": "", "stats": {}}

    flags = needs_tools(question)

    # Stats résumées
    try:
        out["stats"] = robust_stats(df)
    except Exception as e:
        out["messages"].append(f"Erreur stats: {e}")

    # Multi-threading: EDA / REPL / Plots / LLM
    def run_eda_task():
        try:
            eda = IntelligentEDAService(df)
            return eda.full_analysis(engine="all")
        except Exception as e:
            out["messages"].append(f"Erreur EDA: {e}")
            return {}

    def run_repl_task():
        try:
            res = tools_service.execute_python_repl("result = df.describe(include='all')", {"df": df})
            return res.get("locals", {}) if res.get("success") else {}
        except Exception as e:
            out["messages"].append(f"Erreur REPL: {e}")
            return {}

    def run_plot_task():
        charts = []
        try:
            numeric_cols = df.select_dtypes(include="number").columns
            datetime_cols = df.select_dtypes(include="datetime").columns
            for col in numeric_cols:
                fig = generate_distribution_plot(df, col)
                if fig: charts.append(fig)
            for dt_col in datetime_cols:
                for num_col in numeric_cols:
                    fig = generate_time_series_plot(df, dt_col, num_col)
                    if fig: charts.append(fig)
            corr_fig = generate_correlation_plot(df)
            if corr_fig: charts.append(corr_fig)
        except Exception as e:
            out["messages"].append(f"Erreur graphiques: {e}")
        return charts

    def run_llm_task():
        try:
            llm_result = ask_llm(f"Analyse complète: {question}\nStats: {json.dumps(out['stats'])}")
            insights_result = generate_insights(df, out['stats'], question)
            return llm_result, insights_result
        except Exception as e:
            out["messages"].append(f"Erreur LLM/Insights: {e}")
            return "", ""

    futures = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures[executor.submit(run_eda_task)] = "eda"
        if flags["repl"]: futures[executor.submit(run_repl_task)] = "repl"
        if flags["plot"]: futures[executor.submit(run_plot_task)] = "plot"
        futures[executor.submit(run_llm_task)] = "llm"

        for fut in as_completed(futures):
            key = futures[fut]
            try:
                result = fut.result()
                if key == "eda": out["eda_reports"] = result
                elif key == "repl": out["repl"] = result
                elif key == "plot": out["charts"] = result
                elif key == "llm": out["llm"], out["insights"] = result
                out["used"].append(key)
            except Exception as e:
                out["messages"].append(f"Erreur {key}: {e}")

    # Logging interaction sécurisé
    try:
        log_interaction("user", question, out)
    except Exception as e:
        logger.warning(f"Impossible de logger: {e}")

    return out

def analyze_question(df: pd.DataFrame, question: str) -> Dict[str, Any]:
    return smart_agent(df, question)
