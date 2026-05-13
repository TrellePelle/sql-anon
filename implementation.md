# Implementationsplan – sql-anon

---

## Del 1: Analys av kodbasen

### Steg 1 — Analys av grundstruktur, problem och teknisk skuld

### Vad som saknas i nuläget

Projektet är ett tomt git-repo med bara CLAUDE.md. Inget är implementerat.

---

### Styrkor i den planerade strukturen

- Moduluppdelningen (`explain.py`, `anonymize.py`, `deanonymize.py`) följer Single Responsibility Principle tydligt.
- `cli.py` som ett tunt lager ovanpå logiken är rätt — CLI:n ska bara ta emot input och delegera.
- Att mappningsfilen är deterministisk (samma SQL → samma anonymisering) är smart — det gör avanonymisering förutsägbar och testbar.

---

### Potentiella problem och teknisk skuld att adressera från start

**1. Var bor I/O-lagret?**
CLAUDE.md säger "All I/O sker i ett lager" men strukturen listar ingen `io.py` eller `storage.py`. Utan en tydlig fil för detta hamnar filläsning och -skrivning troligen utspridd i modulerna. Lösning: vi behöver besluta — antingen en dedikerad `storage.py`, eller en tydlig konvention om att CLI-lagret ansvarar för all fil-I/O.

**2. Konfigurationshantering saknas**
`explain.py` behöver en API-nyckel för Claude. Var läses den? Ingen `config.py` eller `.env`-hantering finns planerad. Utan detta riskerar API-nyckeln att hamna som hårdkodad eller som ett CLI-argument i klartext. Lösning: en `config.py` som läser från miljövariabel (`ANTHROPIC_API_KEY`) via `os.environ`.

**3. `pyproject.toml` är inte definierad**
Det är grunden för att paketet ska kunna installeras som `sql-anon` och att CLI-kommandot ska fungera. Saknas den, fungerar inget. Den måste på plats tidigt.

**4. Mappningsfilen har inget definierat format eller plats**
`deanonymize.py` ska läsa en JSON-mappningsfil, men var sparas den? Samma katalog som SQL-filen? En fast sökväg? Standardvärdet behöver bestämmas annars blir CLI-gränssnittet inkonsekvent.

**5. Felhantering**
Ingen strategi är definierad. Vad händer om sqlglot inte kan parsa SQL:en? Om mappningsfilen saknas? Om API-nyckeln saknas? Utan ett beslut tidigt blir felhanteringen ojämn.

**6. Teststruktur täcker bara hälften**
Planen har tester för `anonymize` och `deanonymize` men inte för `explain`. Det är OK (den gör API-anrop), men vi bör ha en `conftest.py` med fixtures från start för att undvika duplicering.

---

### Sammanfattning av beslut att ta innan vi planerar

| Fråga | Behöver svar |
|---|---|
| Var bor I/O-lagret? | Separat `storage.py` eller i CLI-lagret? |
| Hur hanteras API-nyckeln? | Miljövariabel (rekommenderat) |
| Var sparas mappningsfilen som standard? | Samma mapp som indata-SQL? Fast sökväg? |
| Felhanteringsstrategi? | Exception + tydligt felmeddelande, eller sys.exit? |

---

## Del 2: Implementationsplan

### Fattade beslut

| Fråga | Beslut |
|---|---|
| Var bor I/O-lagret? | `cli.py` ansvarar för all filläsning/-skrivning. Affärslogiken tar och returnerar strängar. |
| Hur hanteras API-nyckeln? | Miljövariabel `ANTHROPIC_API_KEY`, läses i `config.py` |
| Var sparas mappningsfilen? | Bredvid indata-SQL med suffixet `.mapping.json` (t.ex. `query.sql` → `query.mapping.json`) |
| Felhanteringsstrategi? | Affärslogiken kastar `ValueError`. CLI fångar och skriver ut med `typer.echo` + avslutar med felkod. |

---

### Filer att skapa — i ordning

#### Fas 1: Projektskelett

**1. `pyproject.toml`**
Definierar paketet, beroenden och CLI-entry point (`sql-anon` → `sql_anon.cli:app`).
Beroenden: `typer`, `sqlglot`, `fastapi`, `uvicorn`, `anthropic`.

**2. `sql_anon/__init__.py`**
Tom fil. Gör `sql_anon` till ett Python-paket.

**3. `sql_anon/config.py`**
Läser `ANTHROPIC_API_KEY` från miljön. Kastar `RuntimeError` med förklarande meddelande om nyckeln saknas.

#### Fas 2: Affärslogik

**4. `sql_anon/anonymize.py`**
Funktion: `anonymize(sql: str) -> tuple[str, dict]`
- Parsar SQL med sqlglot
- Traverserar AST och ersätter identifierare (tabeller, kolumner, scheman, alias) med `tabell_1`, `kolumn_1` etc.
- Returnerar anonymiserad SQL-sträng + mappningsdict `{platshållare: originalnamn}`
- Mappningen är deterministisk: samma namn → samma platshållare

**5. `sql_anon/deanonymize.py`**
Funktion: `deanonymize(text: str, mapping: dict) -> str`
- Tar en sträng (svar från tredje part) + mappningsdict
- Byter ut alla platshållare mot originalnamnen
- Inga externa anrop

**6. `sql_anon/explain.py`**
Funktion: `explain(sql: str, client: anthropic.Anthropic) -> str`
- Skickar SQL till Claude API med prompt om att förklara på svenska
- Returnerar förklaringen som sträng
- `client` injiceras som parameter (testbart, inga globala variabler)

#### Fas 3: CLI

**7. `sql_anon/cli.py`**
Tre Typer-kommandon:
- `explain <fil.sql>` — läser filen, anropar `explain()`, skriver ut resultatet
- `anonymize <fil.sql>` — läser filen, anropar `anonymize()`, skriver anonymiserad SQL till stdout, sparar mappningsfil bredvid originalet
- `deanonymize <text.txt> <mappning.json>` — läser båda filerna, anropar `deanonymize()`, skriver ut resultatet

All filläsning och -skrivning sker här, aldrig i affärslogiken.

#### Fas 4: API

**8. `sql_anon/api.py`**
FastAPI-app med tre endpoints som speglar CLI-kommandona:
- `POST /explain` — tar SQL-sträng, returnerar förklaring
- `POST /anonymize` — tar SQL-sträng, returnerar anonymiserad SQL + mappning
- `POST /deanonymize` — tar text + mappning, returnerar avanonymiserad text

#### Fas 5: Tester

**Testramverk**
- `pytest` som testkörare (dev-beroende i `pyproject.toml`)
- `pytest-mock` för att mocka Anthropic-klienten
- Mappstruktur: `tests/` speglar `sql_anon/` (en testfil per modul)

**9. `tests/conftest.py`**
Gemensamma fixtures:
- `simple_sql` — enkel SELECT
- `complex_sql` — JOIN med alias, scheman, subqueries
- `sql_with_literals` — innehåller `WHERE x = 'känsligt värde'`
- `sql_with_comments` — innehåller `-- kommentar`
- `tmp_sql_file` — temporär SQL-fil för CLI-tester
- `mock_anthropic_client` — fejkad klient som returnerar förutbestämda svar

**10. `tests/test_anonymize.py`**

Happy path:
- Tabellnamn ersätts
- Kolumnnamn ersätts
- Schemanamn ersätts
- Alias ersätts
- Determinism: samma SQL → samma mappning över flera anrop
- Samma namn på olika ställen får samma platshållare

Felscenarier:
- Trasig SQL kastar `ValueError` med tydligt meddelande
- Tom sträng hanteras (beslut: kastar fel eller returnerar tomt)
- SQL med bara whitespace

Säkerhetstester (om vi adresserar litteraler och kommentarer):
- Litteraler i WHERE maskeras / maskeras inte (beroende på beslut)
- Kommentarer strippas / behålls (beroende på beslut)

**11. `tests/test_deanonymize.py`**

Happy path:
- Platshållare byts tillbaka
- Text utan platshållare lämnas oförändrad
- Round-trip: `deanonymize(anonymize(sql)) == sql`

Felscenarier:
- Okänd platshållare i texten — kastar fel eller varnar?
- Tom mappning
- Mappning med dubbletter (samma originalnamn pekas till av flera platshållare)

**12. `tests/test_explain.py`**

Med mockad Anthropic-klient:
- Rätt modell och prompt skickas
- SQL inkluderas i prompten
- Returvärdet är strängen från API-svaret
- Fel från API:t kastas vidare som tydligt meddelande

**13. `tests/test_cli.py`**

Använder Typers inbyggda `CliRunner`:
- `anonymize` läser fil, skriver SQL till stdout, skapar `.mapping.json` bredvid
- `deanonymize` läser båda filerna, skriver resultat
- `explain` läser fil, skriver förklaring
- Felfall: fil saknas → tydligt felmeddelande + felkod ≠ 0
- Felfall: saknad `ANTHROPIC_API_KEY` → tydligt meddelande

**14. `tests/test_api.py`**

Använder FastAPIs `TestClient`:
- `POST /anonymize` returnerar SQL + mappning
- `POST /deanonymize` returnerar avanonymiserad text
- `POST /explain` returnerar förklaring (med mockad klient)
- Tom/ogiltig payload → 422
- Trasig SQL → 400 med tydligt felmeddelande

**15. `tests/test_config.py`**

- API-nyckel läses från miljövariabel
- Saknad nyckel → `RuntimeError` med tydligt meddelande

#### Fas 6: Kringfiler

**16. `.env.example`**
Mall med `ANTHROPIC_API_KEY=your-key-here`. Committas. `.env` läggs i `.gitignore`.

**17. `.gitignore`**
Standard Python + `.env` + `*.mapping.json` (känsliga mappningsfiler bör inte committas av misstag).

---

### Implementationsordning

```
pyproject.toml → __init__.py → config.py
    → anonymize.py → deanonymize.py → explain.py
    → cli.py → api.py
    → conftest.py → test_config.py → test_anonymize.py → test_deanonymize.py
    → test_explain.py → test_cli.py → test_api.py
    → .env.example → .gitignore
```

Varje lager bygger på ett redan fungerande lager under. Affärslogiken kan testas utan CLI. CLI kan testas utan API.
