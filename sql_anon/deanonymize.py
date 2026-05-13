import re

_PLACEHOLDER_RE = re.compile(r"\b(?:tabell|kolumn|alias)_\d+\b")


def deanonymize(text: str, mapping: dict[str, str]) -> str:
    """Byt tillbaka platshållare i texten mot originalnamnen från mappningen.

    Använder ordgränser så att t.ex. ``kolumn_1`` inte matchar början av
    ``kolumn_10``.

    Args:
        text: Text som innehåller platshållare av formen ``tabell_N``,
            ``kolumn_N`` eller ``alias_N``.
        mapping: Mappning från platshållare till originalnamn.

    Returns:
        Texten med alla platshållare ersatta av sina originalnamn.

    Raises:
        ValueError: Om texten innehåller platshållare som inte finns i mappningen.
    """
    unknown: list[str] = []

    def replace(match: re.Match[str]) -> str:
        placeholder = match.group(0)
        if placeholder in mapping:
            return mapping[placeholder]
        unknown.append(placeholder)
        return placeholder

    result = _PLACEHOLDER_RE.sub(replace, text)

    if unknown:
        unique = sorted(set(unknown))
        raise ValueError(
            f"Texten innehåller okända platshållare som saknas i mappningen: "
            f"{', '.join(unique)}"
        )

    return result
