import sqlglot
from sqlglot import exp

SUPPORTED_DIALECTS = sorted(
    k.lower()
    for k in sqlglot.dialects.Dialects.__members__.keys()
    if k != "DIALECT"
)


def anonymize(sql: str, dialect: str = "tsql") -> tuple[str, dict[str, str]]:
    """Anonymisera en SQL-fråga genom att ersätta tabell-, kolumn- och aliasnamn.

    Determinismen garanteras av att samma originalnamn (case-insensitivt) alltid
    får samma räknarvärde inom en fråga. Väl-testade dialekter: tsql, postgres.

    Literaler maskeras utan mappning: strängar blir '***' och tal blir 0,
    för att förhindra att PII läcker i den anonymiserade outputen.

    Args:
        sql: SQL-fråga att anonymisera.
        dialect: SQL-dialekt att använda vid parsning och generering (standard: tsql).
            Väl-testade val: tsql (SQL Server), postgres. Övriga dialekter från
            sqlglot stöds men är mindre testade.

    Returns:
        Tuple med (anonymiserad SQL, mappning från platshållare till originalnamn).

    Raises:
        ValueError: Om SQL-strängen är tom, bara whitespace, dialect är okänd,
                    eller SQL inte går att parsa.
    """
    if not sql or not sql.strip():
        raise ValueError("SQL-strängen är tom.")

    if dialect not in SUPPORTED_DIALECTS:
        raise ValueError(
            f"Okänd SQL-dialekt: '{dialect}'. "
            f"Tillgängliga dialekter: {', '.join(SUPPORTED_DIALECTS)}"
        )

    try:
        tree = sqlglot.parse_one(sql, dialect=dialect)
    except sqlglot.errors.ParseError as e:
        # sqlglot inkluderar radnummer och position i felbeskrivningen
        raise ValueError(
            f"Kunde inte parsa SQL ({dialect}): {e}. "
            "Kontrollera att rätt dialekt är vald och att syntaxen är giltig."
        ) from e

    if tree is None:
        raise ValueError("SQL-strängen kunde inte parsas till ett uttryck.")

    mapping: dict[str, str] = {}
    # Lowercase-nyckel för case-insensitiv lookup — "Tabell" och "tabell" får samma platshållare
    lookup: dict[tuple[str, str], str] = {}
    counters = {"tabell": 0, "kolumn": 0, "alias": 0}

    def get_or_create(kind: str, original: str) -> str:
        key = (kind, original.lower())
        if key not in lookup:
            counters[kind] += 1
            placeholder = f"{kind}_{counters[kind]}"
            lookup[key] = placeholder
            mapping[placeholder] = original
        return lookup[key]

    # Pass 1: aliases
    for ta in tree.find_all(exp.TableAlias):
        placeholder = get_or_create("alias", ta.name)
        ta.set("this", exp.to_identifier(placeholder))

    # Pass 2: tabeller
    for t in tree.find_all(exp.Table):
        placeholder = get_or_create("tabell", t.name)
        t.set("this", exp.to_identifier(placeholder))

    # Pass 3: kolumner (inkl. prefix som 'a.namn' eller 'personal.namn')
    for c in tree.find_all(exp.Column):
        col_placeholder = get_or_create("kolumn", c.name)
        c.set("this", exp.to_identifier(col_placeholder))

        if c.table:
            prefix = c.table
            alias_key = ("alias", prefix.lower())
            table_key = ("tabell", prefix.lower())
            if alias_key in lookup:
                c.set("table", exp.to_identifier(lookup[alias_key]))
            elif table_key in lookup:
                c.set("table", exp.to_identifier(lookup[table_key]))

    # Pass 4: literaler — maskeras utan mappning eftersom de kan innehålla PII
    for lit in tree.find_all(exp.Literal):
        if lit.is_string:
            lit.set("this", "***")
        else:
            lit.set("this", "0")

    return tree.sql(dialect=dialect), mapping
