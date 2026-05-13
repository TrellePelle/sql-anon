import sqlglot
from sqlglot import exp


def anonymize(sql: str) -> tuple[str, dict[str, str]]:
    """Anonymisera en SQL-fråga genom att ersätta tabell-, kolumn- och aliasnamn.

    Mappningen är deterministisk: samma originalnamn ger alltid samma platshållare
    inom samma fråga, och samma indata ger alltid samma utdata.

    Args:
        sql: SQL-fråga att anonymisera (förväntas vara T-SQL).

    Returns:
        Tuple med (anonymiserad SQL, mappning från platshållare till originalnamn).

    Raises:
        ValueError: Om SQL-strängen är tom, bara whitespace eller inte går att parsa.
    """
    if not sql or not sql.strip():
        raise ValueError("SQL-strängen är tom.")

    try:
        tree = sqlglot.parse_one(sql, dialect="tsql")
    except sqlglot.errors.ParseError as e:
        raise ValueError(f"Kunde inte parsa SQL: {e}") from e

    if tree is None:
        raise ValueError("SQL-strängen kunde inte parsas till ett uttryck.")

    mapping: dict[str, str] = {}
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

    return tree.sql(dialect="tsql"), mapping
