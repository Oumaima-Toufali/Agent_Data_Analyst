# backend/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN")  # Token GitHub Marketplace
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-4.1")  # Nom du modèle GitHub
    DATA_DIR: str = os.getenv("DATA_DIR", "data")
    CLEAN_DIR: str = os.getenv("CLEAN_DIR", "data/cleaned")
    CHAT_DB: str = os.getenv("CHAT_DB", "data/chat_history.db")

settings = Settings()
