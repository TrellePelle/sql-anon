import json
from pathlib import Path

import anthropic
import typer
from dotenv import load_dotenv

from sql_anon.anonymize import anonymize as anonymize_sql
from sql_anon.config import get_api_key
from sql_anon.deanonymize import deanonymize as deanonymize_text
from sql_anon.explain import explain as explain_sql

# Konfiguration får läsas på CLI-nivå enligt CLAUDE.md ("All I/O sker i ett lager
# – filläsning/skrivning (mappningsfiler, konfiguration) isoleras från affärslogiken").
# load_dotenv läser .env från arbetskatalogen om den finns; affärslogiken läser
# fortfarande bara från os.environ och vet inget om filen.
load_dotenv()

app = typer.Typer(help="Förklara, anonymisera och avanonymisera SQL-frågor.")


def _mapping_path_for(sql_path: Path) -> Path:
    """Returnerar sökvägen till mappningsfilen bredvid SQL-filen."""
    return sql_path.with_suffix(sql_path.suffix + ".mapping.json")


@app.command()
def anonymize(
    sql_file: Path = typer.Argument(
        ..., exists=True, readable=True, help="SQL-fil att anonymisera."
    ),
):
    """Anonymisera SQL och spara mappningsfil bredvid originalet."""
    try:
        sql = sql_file.read_text(encoding="utf-8")
        anonymized, mapping = anonymize_sql(sql)
    except ValueError as e:
        typer.echo(f"Fel: {e}", err=True)
        raise typer.Exit(code=1)

    mapping_path = _mapping_path_for(sql_file)
    mapping_path.write_text(
        json.dumps(mapping, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

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
    try:
        text = text_file.read_text(encoding="utf-8")
        mapping = json.loads(mapping_file.read_text(encoding="utf-8"))
        result = deanonymize_text(text, mapping)
    except (ValueError, json.JSONDecodeError) as e:
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
    try:
        api_key = get_api_key()
        sql = sql_file.read_text(encoding="utf-8")
        client = anthropic.Anthropic(api_key=api_key)
        result = explain_sql(sql, client)
    except (ValueError, RuntimeError) as e:
        typer.echo(f"Fel: {e}", err=True)
        raise typer.Exit(code=1)

    typer.echo(result)


if __name__ == "__main__":
    app()
