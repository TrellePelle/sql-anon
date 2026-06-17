import os


def get_api_key() -> str:
    """Hämta Anthropic API-nyckel från miljövariabeln ANTHROPIC_API_KEY.

    Raises:
        RuntimeError: Om miljövariabeln inte är satt.
    """
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError(
            "Miljövariabeln ANTHROPIC_API_KEY är inte satt. "
            "Sätt den innan du kör kommandot, t.ex. via en .env-fil."
        )
    return key


def get_secret_key() -> str:
    """Hämta API-hemlighet från miljövariabeln API_SECRET_KEY.

    Raises:
        RuntimeError: Om miljövariabeln inte är satt.
    """
    key = os.environ.get("API_SECRET_KEY")
    if not key:
        raise RuntimeError(
            "Miljövariabeln API_SECRET_KEY är inte satt. "
            "Sätt den i .env-filen."
        )
    return key


def get_claude_model() -> str:
    """Hämta Claude-modellnamn från miljövariabeln CLAUDE_MODEL.

    Returnerar 'claude-sonnet-4-5' om variabeln inte är satt.
    """
    return os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-5")


def get_claude_max_tokens() -> int:
    """Hämta max_tokens från miljövariabeln CLAUDE_MAX_TOKENS.

    Returnerar 1024 om variabeln inte är satt eller inte är ett giltigt heltal.
    """
    raw = os.environ.get("CLAUDE_MAX_TOKENS", "1024")
    try:
        return int(raw)
    except ValueError:
        return 1024


def get_file_encoding() -> str:
    """Hämta filkodning från miljövariabeln FILE_ENCODING.

    Returnerar 'utf-8' om variabeln inte är satt.
    """
    return os.environ.get("FILE_ENCODING", "utf-8")


def get_rate_limit_default() -> str:
    """Hämta rate limit för anonymize/deanonymize från RATE_LIMIT_DEFAULT."""
    return os.environ.get("RATE_LIMIT_DEFAULT", "30/minute")


def get_rate_limit_explain() -> str:
    """Hämta rate limit för explain från RATE_LIMIT_EXPLAIN."""
    return os.environ.get("RATE_LIMIT_EXPLAIN", "10/minute")
