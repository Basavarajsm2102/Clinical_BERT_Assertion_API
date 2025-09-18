import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

class TestHealthEndpoint:
    def test_health_check_success(self, client, mock_model):
        with patch('app.main.model', mock_model):
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ["healthy", "unhealthy"]

class TestPredictionEndpoint:
    def test_predict_success(self, client, mock_model):
        with patch('app.main.model', mock_model):
            response = client.post(
                "/predict",
                json={"sentence": "The patient denies chest pain."}
            )
            assert response.status_code == 200
            data = response.json()
            assert "label" in data
            assert "score" in data

    def test_predict_empty_sentence(self, client, mock_model):
        with patch('app.main.model', mock_model):
            response = client.post("/predict", json={"sentence": ""})
            assert response.status_code == 422

    @pytest.mark.parametrize("sentence", [
        "The patient denies chest pain.",
        "He has a history of hypertension.",
        "No signs of pneumonia were observed."
    ])
    def test_predict_various_sentences(self, client, mock_model, sentence):
        with patch('app.main.model', mock_model):
            response = client.post("/predict", json={"sentence": sentence})
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data["score"], float)
            assert 0.0 <= data["score"] <= 1.0

class TestBatchPredictionEndpoint:
    def test_batch_predict_success(self, client, mock_model):
        mock_model.predict_batch.return_value = [
            {"label": "ABSENT", "score": 0.9842},
            {"label": "PRESENT", "score": 0.8976}
        ]

        with patch('app.main.model', mock_model):
            response = client.post(
                "/predict/batch",
                json={"sentences": ["Sentence 1", "Sentence 2"]}
            )
            assert response.status_code == 200
            data = response.json()
            assert len(data["predictions"]) == 2

    def test_batch_predict_empty_list(self, client, mock_model):
        with patch('app.main.model', mock_model):
            response = client.post("/predict/batch", json={"sentences": []})
            assert response.status_code == 422

class TestRootEndpoint:
    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Clinical BERT Assertion API"
        assert "endpoints" in data
