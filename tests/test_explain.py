from unittest.mock import MagicMock

import pytest

from sql_anon.explain import SYSTEM_PROMPT, explain


def _mock_client(response_text: str = "Förklaring av frågan."):
    client = MagicMock()
    client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=response_text)]
    )
    return client


def test_explain_returns_text_from_response():
    client = _mock_client("Frågan hämtar alla rader från personal.")
    result = explain("SELECT * FROM personal", client)
    assert result == "Frågan hämtar alla rader från personal."


def test_explain_sends_sql_in_user_message():
    client = _mock_client()
    explain("SELECT * FROM personal", client)
    call = client.messages.create.call_args
    assert call.kwargs["messages"][0]["content"] == "SELECT * FROM personal"
    assert call.kwargs["messages"][0]["role"] == "user"


def test_explain_uses_swedish_system_prompt():
    client = _mock_client()
    explain("SELECT 1", client)
    call = client.messages.create.call_args
    assert call.kwargs["system"] == SYSTEM_PROMPT


def test_explain_uses_default_claude_model():
    client = _mock_client()
    explain("SELECT 1", client)
    call = client.messages.create.call_args
    assert "claude" in call.kwargs["model"]


def test_explain_accepts_custom_model():
    client = _mock_client()
    explain("SELECT 1", client, model="claude-opus-4-5")
    call = client.messages.create.call_args
    assert call.kwargs["model"] == "claude-opus-4-5"


def test_explain_empty_sql_raises_value_error():
    client = _mock_client()
    with pytest.raises(ValueError):
        explain("", client)


def test_explain_whitespace_sql_raises_value_error():
    client = _mock_client()
    with pytest.raises(ValueError):
        explain("   \n  ", client)
