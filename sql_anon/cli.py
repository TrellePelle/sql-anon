import json
from pathlib import Path

import anthropic
import typer
from dotenv import load_dotenv

from sql_anon.anonymize import anonymize as anonymize_sql
from sql_anon.config import get_api_key, get_claude_model, get_claude_max_tokens, get_file_encoding
from sql_anon.deanonymize import deanonymize as deanonymize_text
from sql_anon.explain import explain as explain_sql

# Konfiguration får läsas på CLI-nivå enligt CLAUDE.md ("All I/O sker i ett lager
# – filläsning/skrivning (mappningsfiler, konfiguration) isoleras från affärslogiken").
# load_dotenv läser .env från arbetskatalogen om den finns; affärslogiken läser
# fortfarande bara från os.environ och vet inget om filen.
load_dotenv()

MAX_FILE_BYTES = 10_000_000  # 10 MB

app = typer.Typer(help="Förklara, anonymisera och avanonymisera SQL-frågor.")


def _mapping_path_for(sql_path: Path) -> Path:
    """Returnerar sökvägen till mappningsfilen bredvid SQL-filen."""
    return sql_path.with_suffix(sql_path.suffix + ".mapping.json")


def _read_file(path: Path) -> str:
    """Läs textfil med felhantering för storlek, encoding och läsrättigheter."""
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            raise ValueError(f"Filen är för stor (max {MAX_FILE_BYTES // 1_000_000} MB).")
    except OSError as e:
        typer.echo(f"Fel: Kunde inte läsa filinformation för '{path}': {e}", err=True)
        raise typer.Exit(code=1)

    encoding = get_file_encoding()
    try:
        return path.read_text(encoding=encoding)
    except UnicodeDecodeError:
        typer.echo(
            f"Fel: Kunde inte läsa '{path}' som {encoding}. "
            "Ange en annan kodning via miljövariabeln FILE_ENCODING.",
            err=True,
        )
        raise typer.Exit(code=1)
    except OSError as e:
        typer.echo(f"Fel: Kunde inte läsa '{path}': {e}", err=True)
        raise typer.Exit(code=1)


def _read_mapping(path: Path) -> dict[str, str]:
    """Läs och validera en JSON-mappningsfil."""
    raw = _read_file(path)
    try:
        mapping = json.loads(raw)
    except json.JSONDecodeError as e:
        typer.echo(f"Fel: Mappningsfilen är inte giltig JSON: {e}", err=True)
        raise typer.Exit(code=1)

    if not isinstance(mapping, dict):
        typer.echo("Fel: Mappningsfilen måste vara ett JSON-objekt.", err=True)
        raise typer.Exit(code=1)

    invalid = {k: v for k, v in mapping.items() if not isinstance(k, str) or not isinstance(v, str)}
    if invalid:
        typer.echo(
            f"Fel: Mappningsfilen innehåller ogiltiga värden (alla nycklar och värden måste vara strängar): "
            f"{list(invalid.keys())[:5]}",
            err=True,
        )
        raise typer.Exit(code=1)

    return mapping


@app.command()
def anonymize(
    sql_file: Path = typer.Argument(
        ..., exists=True, readable=True, help="SQL-fil att anonymisera."
    ),
    dialect: str = typer.Option(
        "tsql",
        help=(
            "SQL-dialekt att använda vid parsning. Standard: tsql.\n\n"
            "Vanliga val: tsql (SQL Server), postgres, mysql, bigquery, "
            "snowflake, redshift, databricks, spark, sqlite.\n\n"
            "Alla dialekter: athena, bigquery, clickhouse, databricks, doris, "
            "dremio, drill, druid, duckdb, dune, exasol, fabric, hive, "
            "materialize, mysql, oracle, postgres, presto, prql, redshift, "
            "risingwave, snowflake, solr, spark, spark2, sqlite, starrocks, "
            "tableau, teradata, trino, tsql."
        ),
    ),
):
    """Anonymisera SQL och spara mappningsfil bredvid originalet."""
    sql = _read_file(sql_file)
    try:
        anonymized, mapping = anonymize_sql(sql, dialect=dialect)
    except ValueError as e:
        typer.echo(f"Fel: {e}", err=True)
        raise typer.Exit(code=1)

    mapping_path = _mapping_path_for(sql_file)
    try:
        mapping_path.write_text(
            json.dumps(mapping, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError as e:
        typer.echo(f"Fel: Kunde inte skriva mappningsfilen '{mapping_path}': {e}", err=True)
        raise typer.Exit(code=1)

    typer.echo(anonymized)
    typer.echo(f"Mappning sparad till: {mapping_path}", err=True)


@app.command()
def deanonymize(
    text_file: Path = typer.Argument(
        ..., exists=True, readable=True, help="Fil med text att avanonymisera."
    ),
    mapping_file: Path = typer.Argument(
        ..., exists=True, readable=True, help="JSON-mappningsfil."
    ),
):
    """Avanonymisera text genom att byta tillbaka platshållare."""
    text = _read_file(text_file)
    mapping = _read_mapping(mapping_file)

    try:
        result = deanonymize_text(text, mapping)
    except ValueError as e:
        typer.echo(f"Fel: {e}", err=True)
        raise typer.Exit(code=1)

    typer.echo(result)


@app.command()
def explain(
    sql_file: Path = typer.Argument(
        ..., exists=True, readable=True, help="SQL-fil att förklara."
    ),
):
    """Förklara SQL-fråga på svenska via Claude API."""
    sql = _read_file(sql_file)
    try:
        api_key = get_api_key()
        client = anthropic.Anthropic(api_key=api_key)
        result = explain_sql(sql, client, model=get_claude_model(), max_tokens=get_claude_max_tokens())
    except (ValueError, RuntimeError) as e:
        typer.echo(f"Fel: {e}", err=True)
        raise typer.Exit(code=1)

    typer.echo(result)


if __name__ == "__main__":
    app()
