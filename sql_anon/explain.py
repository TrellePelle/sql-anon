import anthropic


SYSTEM_PROMPT = (
    "Du är en assistent som förklarar SQL-frågor på enkel svenska. "
    "Förklara vad frågan gör, vilka tabeller och kolumner som används, "
    "och vilket resultat den producerar. Skriv så att någon utan teknisk "
    "bakgrund kan förstå. Använd inte engelska termer i onödan."
)


def explain(
    sql: str,
    client: anthropic.Anthropic,
    model: str = "claude-sonnet-4-5",
    max_tokens: int = 1024,
) -> str:
    """Förklara en SQL-fråga på svenska via Claude API.

    Args:
        sql: SQL-frågan som ska förklaras.
        client: Initierad Anthropic-klient.
        model: Vilken Claude-modell som ska användas.
        max_tokens: Maxlängd på svaret.

    Returns:
        Förklaringen som ren text.

    Raises:
        ValueError: Om SQL-strängen är tom.
    """
    if not sql or not sql.strip():
        raise ValueError("SQL-strängen är tom.")

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": sql}],
    )

    return response.content[0].text
