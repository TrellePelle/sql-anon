# sql-anon

CLI-verktyg och API för att **förklara**, **anonymisera** och **avanonymisera** SQL-frågor.

Användbart när du behöver dela en SQL-fråga med en extern konsult eller support, men tabell- och kolumnnamnen innehåller känslig affärsinformation. Frågan anonymiseras lokalt — ingen SQL skickas till tredje part i anonymiserings- eller avanonymiseringssteget.

## Funktioner

| Kommando | Vad det gör |
|---|---|
| `explain` | Förklarar en SQL-fråga på svenska via Claude API |
| `anonymize` | Byter ut tabell-, kolumn- och aliasnamn mot platshållare som `tabell_1`, `kolumn_1`. Sparar en mappningsfil. |
| `deanonymize` | Tar ett svar med platshållare och byter tillbaka till originalnamnen via mappningsfilen |

## Installation

Kräver Python 3.10+.

```bash
git clone https://github.com/TrellePelle/sql-anon.git
cd sql-anon
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
python -m pip install -e ".[dev]"
```

## Konfiguration

`explain`-kommandot använder Anthropic API och kräver en API-nyckel.

Skapa en `.env`-fil i projektroten:

```
ANTHROPIC_API_KEY=sk-ant-din-nyckel
```

Filen läses automatiskt och är gitignorerad. Skaffa en nyckel på [console.anthropic.com](https://console.anthropic.com).

## Användning (CLI)

### Förklara en SQL-fråga

```bash
sql-anon explain query.sql
```

Skickar SQL till Claude som returnerar en svensk förklaring i klartext.

### Anonymisera

```bash
sql-anon anonymize query.sql
```

Skriver den anonymiserade SQL:en till stdout och sparar mappningen som `query.sql.mapping.json` bredvid originalfilen.

**Exempel:**

Indata (`query.sql`):
```sql
SELECT k.kundnamn, SUM(o.belopp) AS total
FROM kund k
JOIN ordrar o ON o.kund_id = k.id
GROUP BY k.kundnamn
```

Utdata:
```sql
SELECT alias_1.kolumn_1, SUM(alias_2.kolumn_2) AS kolumn_6
FROM tabell_1 AS alias_1
JOIN tabell_2 AS alias_2 ON alias_2.kolumn_3 = alias_1.kolumn_4
GROUP BY alias_1.kolumn_1
```

### Avanonymisera

När du fått ett svar tillbaka från konsulten:

```bash
sql-anon deanonymize svar.txt query.sql.mapping.json
```

Byter tillbaka alla platshållare i `svar.txt` mot originalnamnen.

## Användning (API)

Starta servern:

```bash
uvicorn sql_anon.api:app --reload
```

Swagger-doc finns på `http://127.0.0.1:8000/docs`.

| Endpoint | Body | Respons |
|---|---|---|
| `POST /anonymize` | `{"sql": "..."}` | `{"sql": "...", "mapping": {...}}` |
| `POST /deanonymize` | `{"text": "...", "mapping": {...}}` | `{"text": "..."}` |
| `POST /explain` | `{"sql": "..."}` | `{"explanation": "..."}` |

## Säkerhetsanteckningar

- **Mappningsfilen är känslig.** Den innehåller kopplingen mellan platshållare och originalnamn — om den läcker försvinner hela poängen med anonymiseringen. `*.mapping.json` ligger i `.gitignore` som standard.
- **API:t saknar autentisering** i nuvarande version. Är tänkt för lokal användning eller bakom en proxy.
- **SQL-litteraler maskeras inte.** Värden i `WHERE x = 'hemligt'` skickas vidare oförändrade — anonymisering gäller bara identifierare (tabeller, kolumner, alias).
- **SQL-kommentarer bevaras.** Strippa kommentarer manuellt om de innehåller känslig information.

## Utveckling

Kör tester:

```bash
pytest
```

Projektstruktur:

```
sql-anon/
├── sql_anon/
│   ├── cli.py          # Typer CLI-entry point
│   ├── api.py          # FastAPI-app
│   ├── anonymize.py    # Lokal SQL-anonymisering via sqlglot
│   ├── deanonymize.py  # Avanonymisering via mappningsfil
│   ├── explain.py      # Förklarar SQL via Claude API
│   └── config.py       # Läser ANTHROPIC_API_KEY från miljön
└── tests/
```

## Teknikstack

- **Python 3.10+**
- **[Typer](https://typer.tiangolo.com/)** — CLI
- **[sqlglot](https://sqlglot.com/)** — SQL-parsning (T-SQL-stöd)
- **[FastAPI](https://fastapi.tiangolo.com/)** — API
- **[Anthropic SDK](https://github.com/anthropics/anthropic-sdk-python)** — Claude API för `explain`
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** — `.env`-laddning
