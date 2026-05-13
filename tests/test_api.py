from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from sql_anon.api import app

client = TestClient(app)


def test_anonymize_endpoint_returns_sql_and_mapping():
    response = client.post("/anonymize", json={"sql": "SELECT namn FROM personal"})
    assert response.status_code == 200
    data = response.json()
    assert "tabell_1" in data["sql"]
    assert "personal" in data["mapping"].values()


def test_anonymize_endpoint_invalid_sql_returns_400():
    response = client.post("/anonymize", json={"sql": "INTE GILTIG ###"})
    assert response.status_code == 400


def test_anonymize_endpoint_missing_field_returns_422():
    response = client.post("/anonymize", json={})
    assert response.status_code == 422


def test_deanonymize_endpoint_replaces_placeholders():
    response = client.post(
        "/deanonymize",
        json={"text": "tabell_1", "mapping": {"tabell_1": "personal"}},
    )
    assert response.status_code == 200
    assert response.json()["text"] == "personal"


def test_deanonymize_endpoint_unknown_placeholder_returns_400():
    response = client.post(
        "/deanonymize",
        json={"text": "tabell_99", "mapping": {"tabell_1": "personal"}},
    )
    assert response.status_code == 400


def test_explain_endpoint_returns_explanation(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    with patch("sql_anon.api.anthropic.Anthropic") as mock_cls:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="En förklaring.")]
        )
        mock_cls.return_value = mock_client
        response = client.post("/explain", json={"sql": "SELECT 1"})
    assert response.status_code == 200
    assert response.json()["explanation"] == "En förklaring."


def test_explain_endpoint_missing_api_key_returns_500(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    response = client.post("/explain", json={"sql": "SELECT 1"})
    assert response.status_code == 500
