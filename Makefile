install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

run-backend:
	uvicorn backend.main:app --reload

run-frontend:
	streamlit run frontend/streamlit_app.py
