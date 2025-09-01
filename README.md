# 🤖 AI Data Analyst Agent (GPT-4.1 + LangChain)

**Projet :** Agent IA pour l'analyse et la visualisation de données.  
Basé sur **FastAPI** et **Streamlit**, intégrant **GPT-4.1 via LangChain**, **EDA automatisée**, et génération de graphiques interactifs.

Tout est conçu pour analyser **CSV/Excel**, générer des **insights**, visualiser les données et répondre aux questions **en langage naturel**.

---

## 🚀 Features

- 🧠 Posez des questions sur vos datasets avec GPT-4.1  
- 📊 EDA automatisée (profiling, corrélations, distributions, séries temporelles)  
- 📈 Visualisations interactives (bar, scatter, line, heatmaps)  
- 📂 Upload et nettoyage de données sécurisés  
- 🐍 REPL Python sécurisé pour manipuler les DataFrames  
- ⚙️ Multi-threading et retry pour les appels LLM via LangChain  

---

## 🧱 Tech Stack

| Layer        | Tool Used                                    |
|--------------|----------------------------------------------|
| LLM Engine   | GPT-4.1 via [LangChain](https://www.langchain.com) |
| Web UI       | [Streamlit](https://streamlit.io)            |
| Backend API  | [FastAPI](https://fastapi.tiangolo.com)      |
| Data Analysis| `pandas`, `ydata-profiling`, `sweetviz`, `autoviz` |
| Visualization| `plotly`, `matplotlib`, `seaborn`, `lux`     |
| Database     | SQLite (chat history)                        |

---

## 🗂️ Project Structure

```text
AI-Data-Analyst-Agent/
├── backend/                 
│   ├── api/                 
│   ├── services/            
│   ├── models/              
│   └── utils/               
├── frontend/                
│   └── main.py              
├── tests/                   
│   ├── test_llm_service.py
│   └── test_cleaning_service.py
├── data/                    
├── requirements.txt         
├── .gitignore
├── .env.example             
├── Makefile                 
└── README.md



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
## 🐳 Déploiement avec Docker (optionnel)

Construire et lancer les conteneurs pour backend et frontend :

docker-compose build
docker-compose up
docker-compose down
docker-compose logs -f


⚠ Note : Depuis le frontend Docker, utilisez http://backend:8000 pour appeler le backend.
---
## ⚡ Fonctionnalités principales

- 🔍 Analyse intelligente des données  
- 📊 EDA automatisée (ydata-profiling, Sweetviz, AutoViz, Lux)  
- 📈 Graphiques interactifs (corrélations, distributions, séries temporelles)  
- 🐍 REPL Python sécurisé pour manipuler les DataFrames  
- ⚙️ Robustesse : multi-threading et retry sur appels LLM  

---
##🧠 Exemples d’utilisation

- "Résumez ce dataset en 5 insights clés"

- "Montrez les corrélations entre les variables numériques"

- "Tracez la distribution des âges des clients"

- "Détectez les anomalies dans les séries temporelles des ventes"

## 🔧 Bonnes pratiques suivies

- ✅ Structure claire backend / frontend / tests  
- ✅ Logging et gestion des erreurs  
- ✅ Tests unitaires avec pytest  
- ✅ Documentation reproductible  

---


👩‍💻 Auteur : [Oumaima Toufali](https://www.linkedin.com/in/oumaima-toufali)



