# backend/tests/test_cleaning_service.py
import pytest
from fastapi.testclient import TestClient
from backend.api.clean import router as clean_router
from fastapi import FastAPI
from pathlib import Path
import pandas as pd

# Création d'une app FastAPI temporaire pour le test
app = FastAPI()
app.include_router(clean_router, prefix="/clean")
client = TestClient(app)


@pytest.fixture
def sample_csv(tmp_path):
    file_path = tmp_path / "test.csv"
    df = pd.DataFrame({
        "A": [1, 2, 2, float("inf"), 5],
        "B": ["x", "y", "y", "z", None]
    })
    df.to_csv(file_path, index=False)
    return file_path


def test_clean_df_removes_duplicates_and_inf():
    from backend.services.cleaning_service import clean_df
    df = pd.DataFrame({
        "A": [1, 2, 2, float("inf"), 5],
        "B": ["x", "y", "y", "z", None]
    })
    cleaned = clean_df(df)
    assert cleaned.duplicated().sum() == 0
    assert not cleaned["A"].isin([float("inf"), float("-inf")]).any()


def test_clean_data_creates_file(sample_csv):
    from backend.services.cleaning_service import clean_data
    path = clean_data(str(sample_csv))
    assert Path(path).exists()


def test_clean_endpoint_success(sample_csv):
    payload = {"file_path": str(sample_csv)}
    response = client.post("/clean", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "clean_path" in data
    assert Path(data["clean_path"]).exists()


def test_clean_endpoint_file_not_found():
    payload = {"file_path": "not_existing.csv"}
    response = client.post("/clean", json=payload)
    assert response.status_code == 404
    # ⚠️ message adapté au français
    assert "introuvable" in response.json()["detail"].lower()


def test_clean_endpoint_invalid_format(tmp_path):
    bad_file = tmp_path / "test.txt"
    bad_file.write_text("some text")
    payload = {"file_path": str(bad_file)}
    response = client.post("/clean", json=payload)
    assert response.status_code == 400
    # message attendu pour format non supporté
    assert "format non supporté" in response.json()["detail"].lower()
