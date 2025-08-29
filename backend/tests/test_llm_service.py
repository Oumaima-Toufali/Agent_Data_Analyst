# tests/test_llm_service.py
import pytest
import pandas as pd
import numpy as np
from backend.services.llm_service import analyze_question

# --- Fixtures pour DataFrames ---
@pytest.fixture
def small_df():
    return pd.DataFrame({
        "age": [25, 30, 22, 40, 35],
        "salaire": [30000, 50000, 28000, 70000, 45000],
        "ville": ["Paris", "Lyon", "Paris", "Marseille", "Lyon"],
        "date_embauche": pd.to_datetime(["2019-01-01", "2020-06-15", "2018-03-12", "2021-07-20", "2019-11-05"])
    })

@pytest.fixture
def large_df():
    n = 5000  # test performance gros dataset
    return pd.DataFrame({
        "age": np.random.randint(20, 60, size=n),
        "salaire": np.random.randint(30000, 100000, size=n),
        "ville": np.random.choice(["Paris", "Lyon", "Marseille", "Toulouse"], size=n),
        "date_embauche": pd.to_datetime(np.random.choice(pd.date_range("2015-01-01", "2023-01-01"), size=n))
    })

# --- Tests fonctionnels ---
def test_analyze_question_basic(small_df):
    question = "Fais un résumé statistique du dataset."
    result = analyze_question(small_df, question)
    assert "stats" in result
    assert result["stats"]["rows"] == 5
    assert "age" in result["stats"]["dtypes"]
    assert "llm" in result
    assert isinstance(result["llm"], str)

def test_analyze_question_large(large_df):
    question = "Analyse la tendance des salaires au fil du temps."
    result = analyze_question(large_df, question)
    assert "stats" in result
    assert result["stats"]["rows"] == 5000
    assert "charts" in result
    assert isinstance(result["charts"], list)

def test_tools_usage(small_df):
    question = "Calcule la moyenne et génère un graphique de distribution."
    result = analyze_question(small_df, question)
    # Vérifie que REPL est utilisé
    assert "repl" in result
    assert len(result["repl"]) > 0
    # Vérifie que des graphiques sont générés
    assert "charts" in result
    assert len(result["charts"]) > 0

def test_empty_dataframe():
    import pandas as pd
    empty_df = pd.DataFrame()
    question = "Fais une analyse complète."
    result = analyze_question(empty_df, question)
    assert "error" in result
    assert result["error"] == "DataFrame vide, impossible d’analyser"
