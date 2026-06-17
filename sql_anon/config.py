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
