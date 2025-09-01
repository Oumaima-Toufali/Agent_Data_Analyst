# Frontend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copier et installer les dépendances frontend
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code frontend
COPY . .

# Exposer le port Streamlit
EXPOSE 8501

# Lancer Streamlit
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
