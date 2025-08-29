# backend/utils/chat_logger.py
import sqlite3
import json
from datetime import datetime
from typing import Any
import logging
from backend.config import settings
import os
import pandas as pd

logger = logging.getLogger(__name__)
DB_PATH = settings.CHAT_DB
os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)

def init_db():
    """Initialisation simple de la base"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        role TEXT,
        question TEXT,
        response TEXT
    )
    """)
    conn.commit()
    conn.close()

def serialize_data(data: Any) -> str:
    """Convertit n'importe quelle donnée en texte pour la base"""
    if isinstance(data, pd.DataFrame):
        try:
            return data.to_json(orient="split")
        except Exception:
            try:
                return data.to_csv(index=False)
            except Exception:
                return f"DataFrame({data.shape})"
    elif isinstance(data, dict):
        # Sérialisation récursive des dicts contenant des DataFrames
        try:
            return json.dumps({k: serialize_data(v) for k, v in data.items()})
        except Exception:
            return str(data)
    elif isinstance(data, list):
        # Sérialisation récursive des listes contenant des DataFrames
        try:
            return json.dumps([serialize_data(v) for v in data])
        except Exception:
            return str(data)
    elif hasattr(data, 'to_dict'):
        try:
            return json.dumps(data.to_dict())
        except Exception:
            return str(data)
    else:
        return str(data)

def log_interaction(role: str, question: str, response: Any):
    """Version simplifiée mais robuste"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        
        cur.execute(
            "INSERT INTO chat_history (timestamp, role, question, response) VALUES (?, ?, ?, ?)",
            (
                datetime.utcnow().isoformat(),
                role,
                serialize_data(question),
                serialize_data(response)  # ✅ Gère DataFrames et tout objet
            )
        )
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Erreur logging: {e}")
        # Ne pas faire planter l'application si le logging échoue

# Initialisation auto
init_db()