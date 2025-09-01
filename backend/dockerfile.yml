# Backend Dockerfile
FROM python:3.11-slim

# Répertoire de travail
WORKDIR /app

# Copier et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY . .

# Exposer le port FastAPI
EXPOSE 8000

# Lancer le serveur FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
