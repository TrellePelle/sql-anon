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

    Alla fel från Anthropic-klienten översätts till RuntimeError med
    ett begripligt meddelande, så att anropare (CLI och API) kan visa
    användaren något användbart istället för en rå stack trace.

    Args:
        sql: SQL-frågan som ska förklaras.
        client: Initierad Anthropic-klient.
        model: Vilken Claude-modell som ska användas.
        max_tokens: Maxlängd på svaret.

    Returns:
        Förklaringen som ren text.

    Raises:
        ValueError: Om SQL-strängen är tom.
        RuntimeError: Om Anthropic-anropet misslyckas (auth, rate limit,
            nätverksfel, eller annat fel från Anthropics sida).
    """
    if not sql or not sql.strip():
        raise ValueError("SQL-strängen är tom.")

    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": sql}],
        )
    except anthropic.AuthenticationError as e:
        raise RuntimeError(
            "Anthropic API avvisade nyckeln (autentiseringsfel). "
            "Kontrollera att ANTHROPIC_API_KEY är giltig och inte återkallad."
        ) from e
    except anthropic.PermissionDeniedError as e:
        raise RuntimeError(
            "Anthropic API nekade åtkomst. Kontrollera att nyckeln har "
            "behörighet till modellen som efterfrågas."
        ) from e
    except anthropic.RateLimitError as e:
        raise RuntimeError(
            "Anthropic API returnerade rate limit eller slut på credits. "
            "Vänta en stund eller fyll på credits på console.anthropic.com."
        ) from e
    except anthropic.APIConnectionError as e:
        raise RuntimeError(
            "Kunde inte ansluta till Anthropic API. Kontrollera nätverket "
            "och försök igen."
        ) from e
    except anthropic.APIStatusError as e:
        raise RuntimeError(
            f"Anthropic API returnerade ett fel (status {e.status_code})."
        ) from e
    except anthropic.APIError as e:
        raise RuntimeError(f"Oväntat fel från Anthropic API: {e}") from e

    return response.content[0].text
