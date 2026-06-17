# sql-anon

[![CI](https://github.com/TrellePelle/sql-anon/actions/workflows/ci.yml/badge.svg)](https://github.com/TrellePelle/sql-anon/actions/workflows/ci.yml)

CLI-verktyg och REST API för att **förklara**, **anonymisera** och **avanonymisera** SQL-frågor.

Användbart när du behöver dela en SQL-fråga med en extern konsult eller support, men tabell- och kolumnnamnen innehåller känslig affärsinformation. Frågan anonymiseras **helt lokalt** — ingen SQL-data skickas till tredje part i anonymiserings- eller avanonymiseringssteget.

**Live API:** https://sql-anon-production.up.railway.app/docs

---

## Vad det löser

Inom BI och datalagerarbete behöver man ibland skicka SQL-frågor till externa konsulter eller support. Tabellnamn och kolumnnamn kan då innehålla känslig affärsinformation. Det finns inget enkelt verktyg för att anonymisera och sedan avanonymisera sådana frågor — förrän nu.

**Flödet:**
1. Anonymisera SQL lokalt → dela den anonymiserade versionen
2. Ta emot svar med platshållare från konsulten
3. Avanonymisera svaret lokalt → få tillbaka originalnamnen

---

## Funktioner

| Kommando | Vad det gör |
|---|---|
| `anonymize` | Ersätter tabell-, kolumn- och aliasnamn med platshållare (`tabell_1`, `kolumn_1`). Strängliteraler blir `'***'`, tal blir `0`. Sparar en mappningsfil. |
| `deanonymize` | Tar ett svar med platshållare och byter tillbaka till originalnamnen via mappningsfilen. |
| `explain` | Förklarar en SQL-fråga på svenska via Claude API. |

Stöder 31 SQL-dialekter via sqlglot: `tsql`, `postgres`, `mysql`, `bigquery`, `snowflake`, `redshift`, `databricks`, `spark`, `sqlite` m.fl.

---

## Installation

Kräver Python 3.10+.

```bash
git clone https://github.com/TrellePelle/sql-anon.git
cd sql-anon
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -e ".[dev]"
```

---

## Konfiguration

Skapa en `.env`-fil i projektroten (se `.env.example` för alla alternativ):

```env
# Krävs för explain-kommandot
ANTHROPIC_API_KEY=sk-ant-din-nyckel

# Krävs för /explain-endpointen i API:t
API_SECRET_KEY=din-hemliga-nyckel

# Valfritt — standardvärden visas
CLAUDE_MODEL=claude-sonnet-4-5
CLAUDE_MAX_TOKENS=1024
FILE_ENCODING=utf-8
RATE_LIMIT_DEFAULT=30/minute
RATE_LIMIT_EXPLAIN=10/minute
```

`.env`-filen läses automatiskt och är gitignorerad. Skaffa Anthropic-nyckel på [console.anthropic.com](https://console.anthropic.com).

---

## Användning — CLI

### Anonymisera

```bash
sql-anon anonymize query.sql
sql-anon anonymize query.sql --dialect postgres
```

Skriver anonymiserad SQL till stdout och sparar `query.sql.mapping.json` bredvid originalfilen.

**Exempel:**

Indata (`query.sql`):
```sql
SELECT p.personnummer, p.fornamn
FROM personal p
WHERE p.avdelning = 'HR' AND p.lon > 35000
```

Utdata:
```sql
SELECT alias_1.kolumn_1, alias_1.kolumn_2
FROM tabell_1 AS alias_1
WHERE alias_1.kolumn_3 = '***' AND alias_1.kolumn_4 > 0
```

Mappningsfil (`query.sql.mapping.json`):
```json
{
  "alias_1": "p",
  "kolumn_1": "personnummer",
  "kolumn_2": "fornamn",
  "tabell_1": "personal",
  "kolumn_3": "avdelning",
  "kolumn_4": "lon"
}
```

### Avanonymisera

```bash
sql-anon deanonymize svar.txt query.sql.mapping.json
```

Byter tillbaka alla platshållare i `svar.txt` mot originalnamnen.

### Förklara

```bash
sql-anon explain query.sql
```

Skickar SQL till Claude och returnerar en förklaring på svenska.

---

## Användning — API

Starta servern lokalt:

```bash
uvicorn sql_anon.api:app --reload
```

Swagger-dokumentation finns på `http://127.0.0.1:8000/docs` (eller live på https://sql-anon-production.up.railway.app/docs).

| Endpoint | Autentisering | Body | Respons |
|---|---|---|---|
| `POST /anonymize` | — | `{"sql": "...", "dialect": "tsql"}` | `{"sql": "...", "mapping": {...}}` |
| `POST /deanonymize` | — | `{"text": "...", "mapping": {...}}` | `{"text": "..."}` |
| `POST /explain` | `X-API-Key`-header | `{"sql": "..."}` | `{"explanation": "..."}` |

Rate limiting: 30 req/min för anonymize/deanonymize, 10 req/min för explain.

---

## Säkerhet

- **Anonymisering sker lokalt.** Ingen SQL skickas till externa tjänster i anonymiserings- eller avanonymiseringssteget.
- **Mappningsfilen är känslig.** Den innehåller kopplingen mellan platshållare och originalnamn. `*.mapping.json` är gitignorerad som standard — förvara den säkert.
- **`/explain` kräver API-nyckel.** Sätt `X-API-Key`-headern med värdet från `API_SECRET_KEY`.
- **SQL-kommentarer bevaras.** Strippa kommentarer manuellt om de innehåller känslig information.

---

## Utveckling

```bash
# Kör tester
pytest

# Kör API lokalt med auto-reload
uvicorn sql_anon.api:app --reload
```

Projektstruktur:

```
sql-anon/
├── sql_anon/
│   ├── cli.py          # Typer CLI-entry point
│   ├── api.py          # FastAPI-app med rate limiting och autentisering
│   ├── anonymize.py    # Lokal SQL-anonymisering via sqlglot
│   ├── deanonymize.py  # Avanonymisering via mappningsfil
│   ├── explain.py      # Förklarar SQL via Claude API
│   └── config.py       # Konfiguration från miljövariabler
└── tests/              # 56 tester
```

---

## Teknikstack

| Komponent | Val | Motivering |
|---|---|---|
| Språk | Python 3.10+ | Brett ekosystem, bra SQL-parsers |
| CLI | [Typer](https://typer.tiangolo.com/) | Modernt, typsäkert CLI |
| SQL-parsning | [sqlglot](https://sqlglot.com/) | Lokal parser, stöder 31 dialekter inklusive T-SQL |
| API | [FastAPI](https://fastapi.tiangolo.com/) | Snabbt, automatisk Swagger-dokumentation |
| Rate limiting | [slowapi](https://github.com/laurentS/slowapi) | In-memory rate limiting för FastAPI |
| AI-förklaring | [Anthropic SDK](https://github.com/anthropics/anthropic-sdk-python) | Claude API — bara för explain, ingen SQL-data läcker |
| Deploy | [Railway](https://railway.app/) | Automatisk deploy från GitHub |
