import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO
import base64
from datetime import datetime
import json
import httpx
import plotly
import plotly.io as pio

# ---------------- CONFIG ----------------
BACKEND_URL = "http://localhost:8000"  # adapter si besoin (ne pas inclure /api ici, on l'ajoute dans les appels)

# ---------------- UI HELPERS (inchangés, juste réutilisés) ----------------
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_png_as_page_bg(png_file):
    bin_str = get_base64_of_bin_file(png_file)
    page_bg_img = f'''
    <style>
    .dynamic-title {{
    font-size: 3rem;
    font-weight: bold;
    text-align: center;
    margin-top: 2rem;
    margin-bottom: 2rem;
    color: black;
    min-height: 4rem;
    /* Optionnel: animation fade-in */
    animation: fadeIn 0.5s ease-in forwards;
     }}
    .stApp {{
        background-image: url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    .main-header {{
        font-size: 3rem;
        color: black !important;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }}
    .description {{
        font-size: 1.2rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }}
    .feature-card {{
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin: 1rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }}
    .upload-area {{
        border: 2px dashed #ccc;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        background-color: #f9f9f9;
    }}
    .chat-message {{
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
    }}
    .user-message {{
        background-color: #e3f2fd;
        margin-left: 2rem;
    }}
    .agent-message {{
        background-color: #f1f8e9;
        margin-right: 2rem;
    }}
    .suggestion-button {{
        background-color: #f0f0f0;
        border: 1px solid #ddd;
        border-radius: 20px;
        padding: 0.5rem 1rem;
        margin: 0.2rem;
        cursor: pointer;
    }}
    </style>
    '''
    st.markdown(page_bg_img, unsafe_allow_html=True)

def set_sidebar_background(png_file):
    with open(png_file, "rb") as f:
        data = f.read()
    bin_str = base64.b64encode(data).decode()
    css = f"""
    <style>
    /* Cible le conteneur de la sidebar */
    [data-testid="stSidebar"] > div:first-child {{
        background-image: url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        filter: brightness(0.8);
        height: 100vh;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def add_fixed_logo_top_right(image_path, width=170, top=80, right=20, height=None):
    with open(image_path, "rb") as img_file:
        img_bytes = img_file.read()
    encoded = base64.b64encode(img_bytes).decode()
    height_css = f"height: {height}px;" if height else ""
    css = f"""
    <style>
    .fixed-logo {{
        position: fixed;
        top: {top}px;
        right: {right}px;
        width: {width}px;
        {height_css}
        max-width: 100%;
        z-index: 10000;
        pointer-events: none;
    }}
    </style>
    <img class="fixed-logo" src="data:image/png;base64,{encoded}" />
    """
    st.markdown(css, unsafe_allow_html=True)

# Button style (inchangé)
st.markdown("""
<style>
@keyframes gradientAnimation {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
div.stButton > button[kind="primary"] {
    background: linear-gradient(270deg, #667eea, #764ba2, #667eea);
    background-size: 600% 600%;
    animation: gradientAnimation 4s ease infinite;
    color: white !important;
    font-weight: bold;
    border-radius: 12px;
    padding: 12px 28px;
    border: none;
    box-shadow: 0 8px 15px rgba(118, 75, 162, 0.4);
    cursor: pointer;
    transition: box-shadow 0.3s ease;
}
div.stButton > button[kind="primary"]:hover {
    box-shadow: 0 15px 20px rgba(118, 75, 162, 0.6);
}
</style>
""", unsafe_allow_html=True)

# ---------------- Set backgrounds & logo (if files exist) ----------------
try:
    set_png_as_page_bg("pictures/background.png")
except Exception:
    pass
try:
    set_sidebar_background("pictures/navigationn.png")
except Exception:
    pass
try:
    add_fixed_logo_top_right("pictures/logo.png")
except Exception:
    pass

# Configuration page
st.set_page_config(
    page_title="Data Analyst Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- Session initialization (normalized keys) ----------------
if 'uploaded_data' not in st.session_state:
    st.session_state.uploaded_data = None
if 'uploaded_file_name' not in st.session_state:
    st.session_state.uploaded_file_name = None
if 'original_file_path' not in st.session_state:
    st.session_state.original_file_path = None
if 'clean_file_path' not in st.session_state:
    st.session_state.clean_file_path = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'home'
if 'current_question' not in st.session_state:
    st.session_state.current_question = ''
if 'analysis_summary' not in st.session_state:
    st.session_state.analysis_summary = []

# Sidebar navigation (kept your labels / structure)
st.sidebar.title("Data Analyst Agent")
PAGE_OPTIONS = {'home': "Accueil", 'upload': "Upload", 'chatbot': "Chatbot"}
selected_label = st.sidebar.radio(
    "Menu",
    list(PAGE_OPTIONS.values()),
    index=list(PAGE_OPTIONS.keys()).index(st.session_state.current_page)
)
for key, value in PAGE_OPTIONS.items():
    if value == selected_label:
        st.session_state.current_page = key
        break
# ---------------- Utility: generate unique keys ----------------
import uuid

def unique_key(prefix: str = "key") -> str:
    """
    Génère une clé unique pour Streamlit widgets / charts.
    Exemple: unique_key("download_pdf") -> "download_pdf_a1b2c3d4..."
    """
    return f"{prefix}_{uuid.uuid4().hex}"

# ------------------- PAGES (home, upload, chatbot) -------------------
def home_page():
    st.markdown('<h1 class="main-header"> Explorez vos données intelligemment avec notre Agent IA</h1>', unsafe_allow_html=True)
    st.markdown('<p class="description">Transformez vos données en insights précieux grâce à notre assistant IA intelligent. Posez des questions en langage naturel et obtenez des analyses professionnelles instantanément.</p>', unsafe_allow_html=True)
    st.markdown("###  Démo rapide")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        st.caption("Découvrez comment utiliser l'Agent IA en 2 minutes")
    with st.expander(" Comment poser de bonnes questions ?"):
        st.markdown("""
        *Exemples de questions efficaces :*
        - "Montre-moi les corrélations entre les variables"
        - "Y a-t-il des valeurs aberrantes dans mes données ?"
        - "Crée un graphique des ventes par mois"
        - "Quelles sont les tendances principales ?"
        - "Analyse la distribution de la variable prix"
        """)
    with st.expander(" Exemples d'analyses possibles"):
        st.markdown("""
        *L'Agent IA peut vous aider à :*
        - Analyser les distributions statistiques
        - Identifier les corrélations et tendances
        - Détecter les valeurs aberrantes
        - Créer des visualisations interactives
        - Générer des résumés statistiques
        - Proposer des insights métier
        """)
    with st.expander(" Conseils pour de meilleurs résultats"):
        st.markdown("""
        *Pour optimiser vos analyses :*
        - Assurez-vous que vos données sont bien formatées
        - Posez des questions spécifiques
        - Explorez progressivement vos données
        - N'hésitez pas à demander des clarifications
        """)
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button(" Commencer l'analyse", type="primary", use_container_width=True):
            st.session_state.current_page = 'upload'
            st.rerun()

# ---------------- UPLOAD PAGE ----------------
def upload_page():
    st.markdown('<h1 class="main-header"> Téléchargez vos données</h1>', unsafe_allow_html=True)
    st.markdown("### Sélectionnez votre fichier")
    uploaded_file = st.file_uploader("Choisissez un fichier CSV ou XLSX", type=['csv', 'xlsx'], help="Formats supportés: CSV, Excel (.xlsx)")

    if uploaded_file is not None:
        try:
            # Lecture locale pour aperçu
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            st.success(" Fichier validé avec succès !")
            st.markdown("###  Aperçu des données")
            st.dataframe(df.head(5), use_container_width=True)

            # Statistiques de base
            st.markdown("###  Statistiques de base")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Nombre de lignes", len(df))
            with col2:
                st.metric("Nombre de colonnes", len(df.columns))
            with col3:
                st.metric("Valeurs manquantes", int(df.isnull().sum().sum()))
            with col4:
                st.metric("Taille mémoire", f"{df.memory_usage(deep=True).sum() / 1024:.1f} KB")

            # Types
            st.markdown("####  Types de variables dans le dataset")
            types = df.dtypes.value_counts().to_dict()
            col1, col2, col3 = st.columns(3)
            for i, (dtype, count) in enumerate(types.items()):
                with [col1, col2, col3][i % 3]:
                    st.metric(label=f"{dtype}", value=f"{count} colonnes")

            # Sauvegarder localement en session pour aperçu et information
            st.session_state.uploaded_data = df
            st.session_state.uploaded_file_name = uploaded_file.name

            # Bouton pour envoyer le fichier (UPLOAD -> backend)
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button(" Lancer l'analyse", type="primary", use_container_width=True):
                    # Envoi au backend : POST /api/upload
                    try:
                        with st.spinner("Envoi du fichier au backend et nettoyage..."):
                            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "application/octet-stream")}
                            resp = httpx.post(f"{BACKEND_URL}/api/upload", files=files, timeout=120.0)

                        if resp.status_code == 200:
                            j = resp.json()
                            # Compatibilité avec plusieurs noms possibles renvoyés par le backend
                            file_path = j.get("file_path") 
                            clean_path = j.get("clean_path")
                            st.session_state.original_file_path = file_path

                            resp_clean = httpx.post(f"{BACKEND_URL}/api/clean", json={"file_path": file_path})
                            clean_path = resp_clean.json().get("clean_path")
                            st.session_state.clean_file_path = clean_path

                            st.success("Fichier uploadé et nettoyé avec succès !")
                            st.session_state.current_page = 'chatbot'
                            st.rerun()
                        else:
                            st.error(f"Erreur upload : {resp.status_code} {resp.text}")
                    except Exception as e:
                        st.error(f"Erreur lors de l'upload vers le backend : {e}")
        except Exception as e:
            st.error(f" Erreur lors du traitement du fichier: {str(e)}")
            st.info("Vérifiez que votre fichier est bien formaté et essayez à nouveau.")

# ---------------- CHATBOT PAGE ----------------
def chatbot_page():
    st.markdown('<h1 class="main-header"> Assistant IA d\'Analyse</h1>', unsafe_allow_html=True)

    # Vérifier qu'on a un fichier nettoyé disponible
    if not st.session_state.get("clean_file_path"):
        st.warning("⚠ Aucun fichier nettoyé disponible. Veuillez d'abord télécharger un fichier et le lancer.")
        if st.button(" Aller à l'upload"):
            st.session_state.current_page = 'upload'
            st.rerun()
        return

    # Sidebar : aperçu utilisant uploaded_data
    with st.sidebar:
        st.markdown("### Fichier actuel")
        st.write(f"*Nom du fichier:* {st.session_state.get('uploaded_file_name', 'N/A')}")
        df_preview = st.session_state.get("uploaded_data")
        if df_preview is not None:
            try:
                st.dataframe(df_preview.head(5))
            except Exception:
                st.info("Impossible d'afficher l'aperçu du fichier.")

    # Suggestions
    st.markdown("### Suggestions de questions")
    suggestions = [
        "Montre-moi les corrélations entre les variables",
        "Y a-t-il des valeurs aberrantes ?",
        "Crée un graphique de distribution",
        "Quelles sont les statistiques descriptives ?",
        "Analyse les tendances temporelles",
        "Identifie les patterns intéressants"
    ]
    cols = st.columns(3)
    for i, suggestion in enumerate(suggestions):
        with cols[i % 3]:
            if st.button(suggestion, key=f"suggestion_{i}"):
                st.session_state.current_question = suggestion

    # Conversation
    st.markdown("### Conversation")
    chat_container = st.container()
    with chat_container:
        for i, message in enumerate(st.session_state.get("chat_history", [])):
            role = message.get('role', 'user')
            content = message.get('content', '')
            if role == 'user':
                st.markdown(f'<div class="chat-message user-message"><strong>Vous:</strong> {content}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message agent-message"><strong>Agent IA:</strong> {content}</div>', unsafe_allow_html=True)
                # Plotly charts (JSON)
                for j, chart_json in enumerate(message.get('charts', [])):
                    try:
                        fig = pio.from_json(chart_json)
                        st.plotly_chart(fig, use_container_width=True, key=unique_key(f"chart_{i}_{j}"))
                    except Exception:
                        st.warning("⚠ Impossible d'afficher ce graphique.")
                # charts images base64
                for img_b64 in message.get("charts_base64", []):
                    st.image(base64.b64decode(img_b64), use_column_width=True,key=unique_key(f"img_{i}_{j}"))
                # rapports
                report_paths = message.get("report_paths", {})
                if report_paths:
                    st.markdown("📄 **Rapports générés :**")
                    html_b64 = report_paths.get("html_base64")
                    if html_b64:
                        html_str = base64.b64decode(html_b64).decode("utf-8")
                        st.components.v1.html(html_str, height=600, scrolling=True)
                        st.markdown("---")
                    pdf_b64 = report_paths.get("pdf_base64")
                    if pdf_b64:
                        pdf_bytes = base64.b64decode(pdf_b64)
                        st.download_button(
                            label="📥 Télécharger le rapport PDF",
                            data=pdf_bytes,
                            file_name=f"rapport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            key=unique_key("download_pdf")
                        )

    # Input utilisateur
    user_input = st.text_input("Posez votre question:", value=st.session_state.get('current_question', ''), key="user_input")
    if st.button("Envoyer", type="primary") and user_input:
        st.session_state.chat_history.append({'role': 'user', 'content': user_input, 'timestamp': datetime.now()})
        with st.spinner("L'Agent IA analyse votre question..."):
            # Send to backend USING CLEAN FILE PATH (no file reupload)
            resp = send_to_backend(question=user_input, clean_file_path=st.session_state.clean_file_path)
            # resp is a dict with keys: status, analysis, report_html, report_pdf
            if resp.get("status") == "success":
                analysis = resp.get("analysis", {})
                summary = analysis.get("summary") or analysis.get("llm") or analysis.get("text") or ""
                recommendations = analysis.get("recommendations") or analysis.get("insights") or ""
                charts = analysis.get("charts", []) or []
                stats = analysis.get("stats", {})

                st.session_state.chat_history.append({
                    'role': 'agent',
                    'content': summary if summary else recommendations,
                    'timestamp': datetime.now(),
                    'charts': charts,
                    'charts_base64': analysis.get("charts_base64", []),
                    'stats': stats,
                    'insights': recommendations,
                    'report_paths': {
                        "html_base64": resp.get("report_html"),
                        "pdf_base64": resp.get("report_pdf")
                    }
                })
            else:
                # error returned
                st.session_state.chat_history.append({
                    'role': 'agent',
                    'content': f"Erreur backend: {resp.get('message')}",
                    'timestamp': datetime.now(),
                    'charts': [],
                    'charts_base64': [],
                    'stats': None,
                    'insights': None,
                    'report_paths': {}
                })

        # clear current question and rerun to show results
        st.session_state.current_question = ""
        st.rerun()

# ---------------- Utility: send_to_backend (uses clean_file_path) ----------------
import httpx
import logging

logger = logging.getLogger(__name__)

def send_to_backend(question: str, clean_file_path: str):
    """
    Appelle POST /api/analyze avec JSON {question, clean_file_path}.
    Retourne le JSON décodé ou un dict d'erreur.
    """
    try:
        payload = {"question": question, "clean_file_path": clean_file_path}
        with httpx.Client(timeout=300.0) as client:
            resp = client.post(f"{BACKEND_URL}/api/analyze", json=payload)
            resp.raise_for_status()
            data = resp.json()

            # Vérification simple du format
            if "status" not in data:
                logger.warning(f"Réponse inattendue du backend: {data}")
                return {"status": "error", "message": "Réponse invalide du backend"}
            return data

    except httpx.RequestError as e:
        logger.error(f"Erreur de requête HTTP : {e}")
        return {"status": "error", "message": f"Erreur HTTP : {e}"}
    except httpx.HTTPStatusError as e:
        logger.error(f"Erreur HTTP côté serveur : {e.response.status_code} - {e.response.text}")
        return {"status": "error", "message": f"Erreur serveur : {e.response.status_code}"}
    except Exception as e:
        logger.exception("Erreur inconnue lors de l'appel au backend")
        return {"status": "error", "message": str(e)}

# ---------------- Other utilities (unchanged) ----------------
import streamlit as st
from datetime import datetime
import uuid

def generate_report():
    st.markdown("### 📄 Rapport d'analyse")

    if not st.session_state.get("analysis_summary"):
        st.info("Aucune analyse à inclure dans le rapport.")
        return

    # Création d'un identifiant unique pour le rapport et le bouton
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = uuid.uuid4().hex  # ID unique
    key_button = f"download_report_{timestamp}_{unique_id}"

    report = f"""
# Rapport d'Analyse de Données
*Date:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
*Dataset:* {len(st.session_state.uploaded_data) if st.session_state.get('uploaded_data') is not None else 0} lignes, 
{len(st.session_state.uploaded_data.columns) if st.session_state.get('uploaded_data') is not None else 0} colonnes

## Résumé des Analyses
"""

    for i, analysis in enumerate(st.session_state.analysis_summary, 1):
        report += f"""
### Analyse {i}
*Question:* {analysis['question']}
*Réponse:* {analysis['response']}
*Timestamp:* {analysis['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}

---
"""

    st.markdown(report)

    # Bouton de téléchargement avec clé unique
    st.download_button(
        label="📥 Télécharger le rapport",
        data=report,
        file_name=f"rapport_analyse_{timestamp}.md",
        mime="text/markdown",
        key=key_button
    )


# ---------------- Navigation ----------------
if st.session_state.current_page == 'home':
    home_page()
elif st.session_state.current_page == 'upload':
    upload_page()
elif st.session_state.current_page == 'chatbot':
    chatbot_page()
