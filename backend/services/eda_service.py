# backend/services/eda_service.py
import pandas as pd
import numpy as np
from typing import Dict, Any, Literal
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Librairies EDA
from ydata_profiling import ProfileReport
import sweetviz as sv
from autoviz.AutoViz_Class import AutoViz_Class
import plotly.express as px

# LLM
from backend.services import llm_service

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class IntelligentEDAService:
    """
    Service EDA intelligent et scalable pour datasets tabulaires.
    - Échantillonnage adaptatif
    - Détection robuste des colonnes
    - Rapports ydata, Sweetviz, AutoViz
    - Corrélations et distributions optimisées
    - Insights LLM centralisés
    """

    def __init__(self, df: pd.DataFrame, sample_rows: int = 5000, max_plot_rows: int = 10000):
        self.df = df.copy()
        self.sample_rows = sample_rows
        self.max_plot_rows = max_plot_rows
        if len(self.df) > self.sample_rows:
            self.df = self.df.sample(self.sample_rows, random_state=42)

    # --- Détection améliorée des colonnes ---
    def detect_variable_types(self) -> Dict[str, list]:
        df = self.df.copy()
        numerical, categorical, datetime_cols, text_cols = [], [], [], []

        for col in df.columns:
            dtype = pd.api.types.infer_dtype(df[col], skipna=True)
            if dtype in ["string", "unicode"]:
                # Essayer float
                try:
                    df[col] = df[col].str.replace(",", "").astype(float)
                    numerical.append(col)
                    continue
                except Exception:
                    pass
                # Essayer datetime
                try:
                    tmp = pd.to_datetime(df[col], errors="coerce")
                    if tmp.notna().any():
                        df[col] = tmp
                        datetime_cols.append(col)
                        continue
                except Exception:
                    pass
                # Texte libre
                text_cols.append(col)
            elif pd.api.types.is_numeric_dtype(df[col]):
                numerical.append(col)
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                datetime_cols.append(col)
            else:
                categorical.append(col)

        return {
            "numerical": numerical,
            "categorical": categorical,
            "datetime": datetime_cols,
            "text": text_cols
        }

    # --- Rapports EDA ---
    def generate_profile_report(self, output_path: str = "report_profile.html") -> str:
        try:
            profile = ProfileReport(
                self.df.head(self.sample_rows),
                title="Profiling Report (YData SDK)",
                correlations={"pearson": {"calculate": True}},
                infer_dtypes=True
            )
            profile.to_file(output_path)
            return output_path
        except Exception as e:
            logger.warning(f"Erreur ProfileReport: {e}")
            return f"Erreur ProfileReport: {e}"

    def generate_sweetviz_report(self, output_path: str = "report_sweetviz.html") -> str:
        try:
            report = sv.analyze(self.df.head(self.sample_rows))
            report.show_html(output_path)
            return output_path
        except Exception as e:
            logger.warning(f"Erreur Sweetviz: {e}")
            return f"Erreur Sweetviz: {e}"

    def generate_autoviz_report(self, output_path: str = "autoviz_report") -> str:
        try:
            AV = AutoViz_Class()
            AV.AutoViz(
                filename="", dfte=self.df.head(self.sample_rows), depVar="", save_plot_dir=output_path
            )
            return output_path
        except Exception as e:
            logger.warning(f"Erreur AutoViz: {e}")
            return f"Erreur AutoViz: {e}"

    # --- Détection d’outliers ---
    def detect_outliers(self) -> Dict[str, int]:
        outliers = {}
        numeric_cols = self.detect_variable_types()["numerical"]
        for col in numeric_cols:
            q1, q3 = self.df[col].quantile([0.25, 0.75])
            iqr = q3 - q1
            lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            outliers[col] = self.df[(self.df[col] < lower) | (self.df[col] > upper)].shape[0]
        return outliers

    # --- Corrélations et insights LLM ---
    def correlation_analysis(self, threshold: float = 0.7) -> Dict[str, Any]:
        numeric_cols = self.detect_variable_types()["numerical"]
        corr = self.df[numeric_cols].corr() if numeric_cols else pd.DataFrame()
        fig = px.imshow(corr, text_auto=True, title="Matrice de corrélation") if not corr.empty else None

        strong_relations = {}
        if not corr.empty:
            strong_relations = corr.abs().stack().loc[lambda x: x > threshold].to_dict()
            # Limiter LLM à corrélations fortes pour réduire tokens
            interpretation = llm_service.ask_llm(
                f"Corrélations fortes {strong_relations}. Explique relations et anomalies."
            )
        else:
            interpretation = "Pas de corrélations numériques disponibles."

        return {"figure": fig, "insights": interpretation, "strong_relations": strong_relations}

    # --- Distributions légères ---
    def generate_distribution_plots(self) -> Dict[str, Any]:
        figs = {}
        numeric_cols = self.detect_variable_types()["numerical"]
        df_plot = self.df.head(self.max_plot_rows)
        for col in numeric_cols:
            figs[col] = px.histogram(df_plot, x=col, title=f"Distribution de {col}", marginal="box")
        return figs

    # --- Résumé global ---
    def smart_summary(self) -> Dict[str, Any]:
        return {
            "shape": self.df.shape,
            "missing_values": self.df.isna().sum().to_dict(),
            "dtypes": self.df.dtypes.astype(str).to_dict(),
            "outliers": self.detect_outliers(),
            "variable_types": self.detect_variable_types(),
        }

    # --- Analyse complète configurable ---
    def full_analysis(self, engine: Literal["all", "ydata", "sweetviz", "autoviz"] = "ydata") -> Dict[str, Any]:
        results = {}
        futures = {}
        engines = [engine] if engine != "all" else ["ydata", "sweetviz", "autoviz"]

        with ThreadPoolExecutor(max_workers=3) as executor:
            for eng in engines:
                if eng == "ydata":
                    futures[executor.submit(self.generate_profile_report)] = "profile"
                elif eng == "sweetviz":
                    futures[executor.submit(self.generate_sweetviz_report)] = "sweetviz"
                elif eng == "autoviz":
                    futures[executor.submit(self.generate_autoviz_report)] = "autoviz"

            for f in as_completed(futures):
                key = futures[f]
                try:
                    results[key] = f.result()
                except Exception as e:
                    results[key] = f"Erreur {key}: {e}"

        # Résumé + corrélations + distributions
        summary = self.smart_summary()
        corr_data = self.correlation_analysis()
        dist_data = self.generate_distribution_plots()

        # LLM centralisé pour résumé + recommandations
        prompt = (
            f"Résumé dataset: {summary}\n"
            f"Corrélations fortes: {corr_data.get('strong_relations')}\n"
            "Génère insights et recommandations pratiques."
        )
        llm_output = llm_service.ask_llm(prompt)

        return {
            "summary": summary,
            "eda_reports": results,
            "correlation": corr_data,
            "distributions": dist_data,
            "llm_insights": llm_output
        }
