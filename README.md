# 🤖 AI Data Analyst Agent

**Projet :** Agent IA pour l'analyse et la visualisation de données.  
Basé sur **FastAPI** et **Streamlit**, intégrant des services **LLM**, **EDA automatique**, et la génération de graphiques interactifs.

---

## 📂 Structure du projet

AI-Data-Analyst-Agent/
│
├── backend/                 # API, services et utilitaires
│   ├── api/                 # Endpoints FastAPI
│   ├── services/            # Logique métier (LLM, EDA, outils)
│   ├── models/              # Schémas Pydantic, ML models, etc.
│   └── utils/               # Fonctions utilitaires (charts, logging, etc.)
│
├── frontend/                # Application Streamlit
│   └── main.py
│
├── tests/                   # Tests unitaires avec pytest
│   ├── test_llm_service.py
│   └── test_cleaning_service.py
│
├── .gitignore               # Fichiers ignorés par Git
├── README.md                # Documentation du projet
├── requirements.txt         # Dépendances Python
├── Makefile                 # Commandes pratiques (install, run, test)
└── LICENSE                  # Licence du projet


## 🚀 Installation

1️⃣ Cloner le projet :
git clone https://github.com/ton-utilisateur/AI-Data-Analyst-Agent.git
cd AI-Data-Analyst-Agent

2️⃣ Créer un environnement virtuel :
python -m venv .venv
# Linux / Mac
source .venv/bin/activate
# Windows
.venv\Scripts\activate

3️⃣ Installer les dépendances :
pip install -r requirements.txt

---
## 🔑 Configuration `.env`

Le projet utilise un fichier `.env` pour stocker les variables sensibles et les chemins de données.

**Exemple de contenu `.env` :**

# Token GitHub (NE JAMAIS COMMITTER VRAI TOKEN)
GITHUB_TOKEN=your_github_token_here

# Modèle LLM
MODEL_NAME=gpt-4.1

# Endpoint GitHub pour inference
GITHUB_ENDPOINT=https://models.github.ai/inference

# Chemins des données
DATA_DIR=data
CLEAN_DIR=data/cleaned
CHAT_DB=data/chat_history.db


## 🏃‍♂️ Lancer le projet

Backend (FastAPI) :
uvicorn backend.main:app --reload

Frontend (Streamlit) :
streamlit run frontend/main.py

---

## ✅ Tests

pytest tests/ -v

---

## ⚡ Fonctionnalités principales

- 🔍 Analyse intelligente des données  
- 📊 EDA automatisée (ydata-profiling, Sweetviz, AutoViz, Lux)  
- 📈 Graphiques interactifs (corrélations, distributions, séries temporelles)  
- 🐍 REPL Python sécurisé pour manipuler les DataFrames  
- ⚙️ Robustesse : multi-threading et retry sur appels LLM  

---

## 🔧 Bonnes pratiques suivies

- ✅ Structure claire backend / frontend / tests  
- ✅ Logging et gestion des erreurs  
- ✅ Tests unitaires avec pytest  
- ✅ Documentation reproductible  

---


👩‍💻 Auteur : [Oumaima Toufali](https://www.linkedin.com/in/oumaima-toufali)



