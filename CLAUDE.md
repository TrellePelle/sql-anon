# CLAUDE.md

## Vad projektet gör och vilket problem det löser

`sql-anon` är ett CLI-verktyg med tillhörande API-endpoint för att:

1. **Förklara** SQL-frågor på plain svenska – användbart för att dokumentera rapporter och frågor utan att behöva förstå koden i detalj.
2. **Anonymisera** SQL-frågor lokalt – ersätter tabellnamn, kolumnnamn, schemanamn och alias med generiska platshållare (`tabell_1`, `kolumn_1` etc.) så att frågan kan skickas till tredje part utan att känslig information läcker.
3. **Avanonymisera** – tar ett svar från tredje part som innehåller platshållare och byter tillbaka till de riktiga namnen via en lokal mappningsfil.

**Problemet det löser:** Inom BI och datalagerarbete behöver man ibland skicka SQL-frågor till externa konsulter eller support. Då kan tabellnamn och kolumnnamn innehålla känslig affärsinformation. Det finns inget enkelt verktyg för att anonymisera och sedan avanonymisera sådana frågor.

---

## Teknikstack och varför

| Komponent | Val | Motivering |
|---|---|---|
| Språk | Python | Bra SQL-parsers finns, stort ekosystem, enkelt att distribuera |
| CLI | Typer | Modernt, typsäkert CLI-bibliotek med bra hjälptexter |
| SQL-parsning | sqlglot | Lokal parser som stödjer T-SQL (SQL Server/SSRS), ingen data lämnar maskinen |
| API | FastAPI | Snabbt, modernt, automatisk API-dokumentation via Swagger |
| AI-förklaring | Anthropic API (Claude) | Endast för förklaringsfunktionen – ingen SQL-data skickas för anonymisering |
| Deploy | Render / Railway | Gratis tier, enkel deployment av FastAPI-app |

---

## Arkitekturprinciper

- **Anonymisering sker alltid lokalt** – ingen SQL-data skickas till externa tjänster i anonymiserings- eller avanonymiseringssteget
- **En funktion per modul** – `explain.py`, `anonymize.py`, `deanonymize.py` gör var sin sak
- **All I/O sker i ett lager** – filläsning/skrivning (mappningsfiler, konfiguration) isoleras från affärslogiken
- **Mappningsfilen är deterministisk** – samma SQL ger alltid samma anonymisering, vilket gör avanonymisering förutsägbar
- **Funktioner ska göra en sak** – ingen funktion hanterar både parsning och utskrift
- **Inga globala variabler** – state skickas explicit som parametrar

---

## Saker agenten INTE ska göra

- **Byt inte ut sqlglot mot ett annat SQL-parsningsbibliotek** utan att fråga – det påverkar T-SQL-stödet
- **Skicka inte SQL-data till externa API:er** i anonymiserings- eller avanonymiseringssteget – det bryter mot hela syftet med verktyget
- **Lägg inte till externa beroenden** utan att fråga först
- **Byt inte databasmotor** – projektet är inte kopplat till någon databas, mappningar sparas som lokala JSON-filer
- **Ändra inte CLI-kommandonamnen** (`explain`, `anonymize`, `deanonymize`) utan att fråga – de är en del av det publika gränssnittet
- **Generera inte hårdkodade tabellnamn eller exempeldata** som ser ut som riktig affärsdata

---

## Projektstruktur (mål)

```
sql-anon/
├── CLAUDE.md
├── README.md
├── pyproject.toml
├── sql_anon/
│   ├── __init__.py
│   ├── cli.py          # Typer CLI-entry point
│   ├── api.py          # FastAPI-app
│   ├── explain.py      # Förklarar SQL via Claude API
│   ├── anonymize.py    # Lokal SQL-anonymisering via sqlglot
│   └── deanonymize.py  # Avanonymisering via mappningsfil
└── tests/
    ├── test_anonymize.py
    └── test_deanonymize.py
```
