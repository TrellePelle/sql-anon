import pytest

from sql_anon.config import get_api_key


def test_get_api_key_returns_value_from_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-nyckel-123")
    assert get_api_key() == "test-nyckel-123"


def test_get_api_key_raises_when_missing(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        get_api_key()
