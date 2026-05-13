from unittest.mock import MagicMock

import anthropic
import httpx
import pytest

from sql_anon.explain import SYSTEM_PROMPT, explain


def _http_response(status_code: int) -> httpx.Response:
    """Bygg en minimal httpx.Response som Anthropics undantag kräver."""
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    return httpx.Response(status_code=status_code, request=request)


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


def test_explain_authentication_error_becomes_runtime_error():
    client = _mock_client()
    client.messages.create.side_effect = anthropic.AuthenticationError(
        "Invalid API key", response=_http_response(401), body=None
    )
    with pytest.raises(RuntimeError, match="autentiseringsfel"):
        explain("SELECT 1", client)


def test_explain_permission_denied_becomes_runtime_error():
    client = _mock_client()
    client.messages.create.side_effect = anthropic.PermissionDeniedError(
        "No access to model", response=_http_response(403), body=None
    )
    with pytest.raises(RuntimeError, match="nekade åtkomst"):
        explain("SELECT 1", client)


def test_explain_rate_limit_becomes_runtime_error():
    client = _mock_client()
    client.messages.create.side_effect = anthropic.RateLimitError(
        "Rate limited", response=_http_response(429), body=None
    )
    with pytest.raises(RuntimeError, match="rate limit"):
        explain("SELECT 1", client)


def test_explain_connection_error_becomes_runtime_error():
    client = _mock_client()
    client.messages.create.side_effect = anthropic.APIConnectionError(
        request=httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    )
    with pytest.raises(RuntimeError, match="ansluta"):
        explain("SELECT 1", client)


def test_explain_generic_status_error_becomes_runtime_error():
    client = _mock_client()
    client.messages.create.side_effect = anthropic.APIStatusError(
        "Internal server error", response=_http_response(500), body=None
    )
    with pytest.raises(RuntimeError, match="500"):
        explain("SELECT 1", client)


def test_explain_runtime_error_preserves_original_exception_via_from():
    client = _mock_client()
    original = anthropic.AuthenticationError(
        "Invalid API key", response=_http_response(401), body=None
    )
    client.messages.create.side_effect = original
    with pytest.raises(RuntimeError) as excinfo:
        explain("SELECT 1", client)
    assert excinfo.value.__cause__ is original
