# sql-anon

[![CI](https://github.com/TrellePelle/sql-anon/actions/workflows/ci.yml/badge.svg)](https://github.com/TrellePelle/sql-anon/actions/workflows/ci.yml)

CLI-verktyg och REST API för lokal SQL-anonymisering — dela känsliga SQL-frågor med externa konsulter utan att affärskritisk information läcker.

**Live:** https://sql-anon-production.up.railway.app/docs

---

## Vad det gör

Anonymiserar SQL-frågor helt lokalt genom att ersätta tabell-, kolumn- och aliasnamn med generiska platshållare (`tabell_1`, `kolumn_1`). Strängliteraler och tal maskeras så att PII inte läcker. En mappningsfil sparas lokalt och används sedan för att byta tillbaka originalnamnen när konsultens svar kommer. Stöder 31 SQL-dialekter inklusive T-SQL, PostgreSQL, MySQL, BigQuery och Snowflake.

---

## Kom igång

### Krav

- Python 3.10+
- Anthropic API-nyckel (krävs bara för `explain`-kommandot)

### Installation

```bash
git clone https://github.com/TrellePelle/sql-anon.git
cd sql-anon
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -e ".[dev]"
```

### Konfiguration

Skapa en `.env`-fil i projektets rot:

```env
ANTHROPIC_API_KEY=sk-ant-din-nyckel
API_SECRET_KEY=din-hemliga-nyckel
```

Alla tillgängliga variabler finns listade i `.env.example`.

### Kör projektet

```bash
# CLI
sql-anon anonymize query.sql
sql-anon deanonymize svar.txt query.sql.mapping.json
sql-anon explain query.sql

# API lokalt
uvicorn sql_anon.api:app --reload
```

---

## Användning

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

### Avanonymisera

```bash
sql-anon deanonymize svar.txt query.sql.mapping.json
```

### Förklara

```bash
sql-anon explain query.sql
```

### API

| Endpoint | Autentisering | Body | Respons |
|---|---|---|---|
| `POST /anonymize` | — | `{"sql": "...", "dialect": "tsql"}` | `{"sql": "...", "mapping": {...}}` |
| `POST /deanonymize` | — | `{"text": "...", "mapping": {...}}` | `{"text": "..."}` |
| `POST /explain` | `X-API-Key`-header | `{"sql": "..."}` | `{"explanation": "..."}` |

Rate limiting: 30 req/min för anonymize/deanonymize, 10 req/min för explain.

---

## Arkitektur

CLI och API är tunna I/O-lager. All affärslogik finns i egna moduler som tar och returnerar strängar — inga beroenden till filsystem eller HTTP i affärslogiken. Mappningsfilen är deterministisk: samma SQL ger alltid samma platshållare, vilket gör avanonymisering förutsägbar.

```
sql-anon/
├── sql_anon/
│   ├── cli.py          # Typer CLI — läser filer, anropar affärslogik
│   ├── api.py          # FastAPI — rate limiting, autentisering, routing
│   ├── anonymize.py    # Lokal SQL-anonymisering via sqlglot AST-traversering
│   ├── deanonymize.py  # Avanonymisering via regex och mappningsfil
│   ├── explain.py      # Förklarar SQL via Claude API
│   └── config.py       # Konfiguration från miljövariabler med fallbacks
└── tests/              # 56 tester
```

---

## Teknisk stack

| Komponent | Val | Anledning |
|---|---|---|
| Språk | Python 3.10+ | Brett ekosystem, bra SQL-parsers |
| CLI | Typer | Modernt, typsäkert CLI med automatiska hjälptexter |
| SQL-parsning | sqlglot | Lokal parser, stöder 31 dialekter inklusive T-SQL |
| API | FastAPI | Snabbt, automatisk Swagger-dokumentation |
| Rate limiting | slowapi | In-memory rate limiting för FastAPI |
| AI-förklaring | Anthropic SDK | Claude API — bara för explain, ingen SQL-data läcker |
| Deploy | Railway | Automatisk deploy från GitHub |
| CI | GitHub Actions | Kör 56 tester vid varje push |

---

## Begränsningar

- **SQL-kommentarer bevaras.** Kommentarer i SQL-koden anonymiseras inte — strippa dem manuellt om de innehåller känslig information.
- **Mappningsfilen är känslig.** Den innehåller kopplingen mellan platshållare och originalnamn. Läcker den försvinner hela poängen med anonymiseringen. Filen är gitignorerad men du ansvarar för att förvara den säkert.
- **In-memory rate limiting.** Nollställs vid omstart och fungerar inte bakom en load balancer med flera instanser.
- **Inte testat mot alla 31 dialekter.** Väl-testade dialekter är `tsql` och `postgres`. Övriga dialekter stöds via sqlglot men kan ge oväntad output för kantfall.

---

## Utvecklat med

[Claude Code](https://claude.ai/code) (agentdriven utveckling) som del av kursen *Next-Generation Software Development with AI*.
