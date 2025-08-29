# backend/services/report_service.py

import os
import json
import base64
import platform
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

import pdfkit
import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape
import streamlit as st

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# -----------------------------
# Templates
# -----------------------------
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
os.makedirs(TEMPLATE_DIR, exist_ok=True)
BASE_TEMPLATE = os.path.join(TEMPLATE_DIR, "report_template.html")

env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html", "xml"])
)

# Template minimal si inexistant
if not os.path.exists(BASE_TEMPLATE):
    with open(BASE_TEMPLATE, "w", encoding="utf-8") as f:
        f.write("""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>{{ title }}</title>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<style>
body { font-family: Arial, sans-serif; margin: 20px; }
h1, h2, h3 { color: #2c3e50; }
table { border-collapse: collapse; margin-bottom: 20px; width: 100%; }
th, td { border: 1px solid #ccc; padding: 6px 10px; text-align: center; font-size: 14px; }
th { background-color: #f8f9fa; }
.section { margin-bottom: 30px; }
.insight { background: #f0f9ff; border-left: 4px solid #007acc; padding: 10px; margin-bottom: 15px; }
</style>
</head>
<body>
<h1>{{ title }}</h1>
<p>{{ description }}</p>

{% if stats %}
<div class="section">
<h2>📊 Statistiques descriptives</h2>
<table>
<tr>
<th>Stat</th>
{% for col in stats.keys() %}
<th>{{ col }}</th>
{% endfor %}
</tr>
{% for stat_name, values in stats.items() %}
<tr>
<td>{{ stat_name }}</td>
{% for col in stats.keys() %}
<td>{{ values.get(col, 'N/A') }}</td>
{% endfor %}
</tr>
{% endfor %}
</table>
</div>
{% endif %}

{% if summary_interpretation %}
<div class="section">
<h2>📝 Analyse du dataset</h2>
<div class="insight">{{ summary_interpretation | safe }}</div>
</div>
{% endif %}

{% if recommendations %}
<div class="section">
<h2>💡 Recommandations</h2>
<div class="insight">{{ recommendations | safe }}</div>
</div>
{% endif %}

{% if charts %}
<div class="section">
<h2>📈 Graphiques</h2>
{% for chart in charts %}
<div id="chart-{{ loop.index0 }}" style="width:100%;height:400px;"></div>
<script>
var figure = {{ chart | safe }};
Plotly.newPlot('chart-{{ loop.index0 }}', figure.data, figure.layout);
</script>
{% endfor %}
</div>
{% endif %}
</body>
</html>""")

# -----------------------------
# wkhtmltopdf
# -----------------------------
def get_wkhtmltopdf_path() -> Optional[str]:
    system = platform.system()
    if system == "Windows":
        path = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
        return path if os.path.exists(path) else None
    else:
        from shutil import which
        return which("wkhtmltopdf")

# -----------------------------
# Génération rapport principal
# -----------------------------
def generate_report(
    question: str,
    response: Union[str, Dict[str, Any]],
    df: Optional[pd.DataFrame] = None,
    chart_jsons: Optional[List[Union[str, Dict]]] = None,
    stats: Optional[Dict[str, Any]] = None,
    recommendations: Optional[str] = None,
    summary_interpretation: Optional[str] = None,
    output_dir: str = "backend/reports",
    filename: Optional[str] = None,
    to_html: bool = True,
    to_pdf: bool = True
) -> Dict[str, Optional[str]]:

    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = filename or f"report_{timestamp}"

    # Génération stats si absentes
    if stats is None and df is not None:
        try:
            stats = df.describe(include="all", datetime_is_numeric=True).to_dict()
        except Exception as e:
            logger.warning(f"Impossible de générer les stats: {e}")
            stats = {}

    # Conversion charts JSON
    charts = []
    if chart_jsons:
        for c in chart_jsons:
            try:
                charts.append(json.loads(c) if isinstance(c, str) else c)
            except Exception as e:
                logger.warning(f"Échec conversion chart JSON: {e}")

    # Texte d’analyse
    if isinstance(response, dict):
        summary_interpretation = response.get("summary_interpretation", summary_interpretation)
        recommendations = response.get("recommendations", recommendations)
        response_text = response.get("summary_interpretation", "")
    else:
        response_text = response

    # HTML via Jinja2
    html_file = os.path.join(output_dir, f"{filename}.html")
    template = env.get_template("report_template.html")
    html_content = template.render(
        title="Rapport d'Analyse de Données",
        description=f"Analyse de la question : {question}",
        text=response_text,
        stats=stats,
        charts=charts,
        summary_interpretation=summary_interpretation,
        recommendations=recommendations
    )
    if to_html:
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)

    # Génération PDF
    pdf_file = os.path.join(output_dir, f"{filename}.pdf") if to_pdf else None
    if to_pdf:
        wk_path = get_wkhtmltopdf_path()
        if wk_path:
            try:
                config = pdfkit.configuration(wkhtmltopdf=wk_path)
                pdfkit.from_file(html_file, pdf_file, configuration=config)
            except Exception as e:
                logger.error(f"Échec génération PDF: {e}")
                pdf_file = None
        else:
            logger.error("wkhtmltopdf non trouvé, impossible de générer le PDF.")
            pdf_file = None

    # Base64
    html_b64 = base64.b64encode(html_content.encode("utf-8")).decode("utf-8")
    pdf_b64 = None
    if pdf_file and os.path.exists(pdf_file):
        with open(pdf_file, "rb") as f:
            pdf_b64 = base64.b64encode(f.read()).decode("utf-8")

    return {
        "html": html_file if to_html else None,
        "pdf": pdf_file,
        "html_content": html_content,
        "html_base64": html_b64,
        "pdf_base64": pdf_b64
    }

# -----------------------------
# Fonctions utilitaires
# -----------------------------
def save_report_html(report_data: Dict[str, Optional[str]], output_dir: str = "backend/reports") -> str:
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_file = os.path.join(output_dir, f"rapport_{timestamp}.html")
    html_content = report_data.get("html_content", "<p>Pas de contenu</p>")
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    return html_file

def save_report_pdf(report_data: Dict[str, Optional[str]], output_dir: str = "backend/reports") -> Optional[str]:
    html_file = save_report_html(report_data, output_dir)
    pdf_file = html_file.replace(".html", ".pdf")
    wk_path = get_wkhtmltopdf_path()
    if wk_path:
        try:
            config = pdfkit.configuration(wkhtmltopdf=wk_path)
            pdfkit.from_file(html_file, pdf_file, configuration=config)
            return pdf_file
        except Exception as e:
            logger.error(f"Échec génération PDF: {e}")
            return None
    else:
        logger.error("wkhtmltopdf non trouvé, impossible de générer le PDF.")
        return None

def display_report(report_data: Dict[str, Optional[str]]):
    html_content = report_data.get("html_content")
    pdf_file = report_data.get("pdf")
    if html_content:
        st.markdown("### 📄 Rapport généré")
        st.components.v1.html(html_content, height=800, scrolling=True)
    if pdf_file and os.path.exists(pdf_file):
        with open(pdf_file, "rb") as f:
            pdf_bytes = f.read()
        st.download_button(
            label="📥 Télécharger le PDF",
            data=pdf_bytes,
            file_name=os.path.basename(pdf_file),
            mime="application/pdf"
        )
