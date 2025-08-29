# backend/utils/chart_generator.py
import pandas as pd
import plotly.express as px
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)
MAX_ROWS_SAMPLE = 5000  # Limite pour gros datasets


def _sample_df(df: pd.DataFrame) -> pd.DataFrame:
    """Échantillonne le DataFrame si trop grand pour Plotly."""
    if len(df) > MAX_ROWS_SAMPLE:
        logger.info(f"Échantillonnage du DataFrame à {MAX_ROWS_SAMPLE} lignes pour performance.")
        return df.sample(n=MAX_ROWS_SAMPLE, random_state=42)
    return df


def generate_correlation_plot(df: pd.DataFrame, method: str = "pearson") -> Optional[Dict]:
    """Génère une matrice de corrélation."""
    try:
        if df.empty or df.select_dtypes(include=["number"]).shape[1] < 2:
            logger.warning("Pas assez de colonnes numériques pour corrélation.")
            return None

        df = _sample_df(df)
        corr = df.select_dtypes(include=["number"]).corr(method=method)
        fig = px.imshow(
            corr, text_auto=True, aspect="auto",
            title=f"Matrice de corrélation ({method})",
            color_continuous_scale="RdBu_r", zmin=-1, zmax=1
        )
        logger.info("Matrice de corrélation générée.")
        return {"success": True, "fig_json": fig.to_json()}
    except Exception as e:
        logger.error(f"Erreur generate_correlation_plot: {e}")
        return {"success": False, "error": str(e)}


def generate_distribution_plot(
    df: pd.DataFrame, column: str, top_n: int = 20, plot_type: str = "hist"
) -> Optional[Dict]:
    """Histogramme, boxplot ou bar plot pour une colonne."""
    try:
        if df.empty or column not in df.columns:
            logger.warning(f"Colonne '{column}' absente ou DataFrame vide.")
            return None

        df = _sample_df(df)

        if pd.api.types.is_numeric_dtype(df[column]):
            if plot_type == "hist":
                fig = px.histogram(df, x=column, nbins=30, marginal="box",
                                   title=f"Distribution de {column}", color_discrete_sequence=["#636EFA"])
            else:
                fig = px.box(df, y=column, title=f"Boxplot de {column}", color_discrete_sequence=["#EF553B"])
        else:
            value_counts = df[column].value_counts().nlargest(top_n).reset_index()
            value_counts.columns = [column, "count"]
            fig = px.bar(value_counts, x=column, y="count",
                         title=f"Distribution catégorielle de {column} (Top {top_n})",
                         color="count", color_continuous_scale="Viridis")

        logger.info(f"Distribution plot généré pour '{column}'.")
        return {"success": True, "fig_json": fig.to_json()}
    except Exception as e:
        logger.error(f"Erreur generate_distribution_plot: {e}")
        return {"success": False, "error": str(e)}


def generate_scatter_plot(df: pd.DataFrame, x: str, y: str, color: Optional[str] = None) -> Optional[Dict]:
    """Scatter plot ou strip plot si colonnes non numériques."""
    try:
        if df.empty or any(col not in df.columns for col in [x, y]):
            logger.warning(f"Colonnes '{x}' ou '{y}' absentes ou DataFrame vide.")
            return None

        df = _sample_df(df)

        if pd.api.types.is_numeric_dtype(df[x]) and pd.api.types.is_numeric_dtype(df[y]):
            fig = px.scatter(df, x=x, y=y, color=color, title=f"Scatter Plot : {x} vs {y}", trendline="ols")
        else:
            fig = px.strip(df, x=x, y=y, color=color, title=f"Scatter/Jitter Plot : {x} vs {y}", stripmode="overlay")

        logger.info(f"Scatter plot généré pour '{x}' vs '{y}'.")
        return {"success": True, "fig_json": fig.to_json()}
    except Exception as e:
        logger.error(f"Erreur generate_scatter_plot: {e}")
        return {"success": False, "error": str(e)}


def generate_time_series_plot(
    df: pd.DataFrame, date_col: str, value_col: str, color: Optional[str] = None
) -> Optional[Dict]:
    """Graphique de série temporelle."""
    try:
        if df.empty or any(col not in df.columns for col in [date_col, value_col]):
            logger.warning(f"Colonnes '{date_col}' ou '{value_col}' absentes ou DataFrame vide.")
            return None

        df = _sample_df(df)
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        if df[date_col].isnull().all():
            logger.warning(f"Colonne '{date_col}' ne contient aucune date valide.")
            return None

        df = df.sort_values(date_col)
        fig = px.line(df, x=date_col, y=value_col, color=color,
                      title=f"Série temporelle : {value_col}", markers=True)
        logger.info(f"Time series plot généré pour '{value_col}' selon '{date_col}'.")
        return {"success": True, "fig_json": fig.to_json()}
    except Exception as e:
        logger.error(f"Erreur generate_time_series_plot: {e}")
        return {"success": False, "error": str(e)}
