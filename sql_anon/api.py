import anthropic
from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from sql_anon.anonymize import anonymize as anonymize_sql
from sql_anon.config import get_api_key, get_secret_key
from sql_anon.deanonymize import deanonymize as deanonymize_text
from sql_anon.explain import explain as explain_sql

MAX_SQL_CHARS = 100_000
MAX_TEXT_CHARS = 100_000
MAX_MAPPING_ITEMS = 10_000

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="sql-anon",
    description="API för att förklara, anonymisera och avanonymisera SQL.",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_secret_key(key: str | None = Security(_api_key_header)) -> None:
    try:
        expected = get_secret_key()
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    if key != expected:
        raise HTTPException(status_code=401, detail="Ogiltig eller saknad API-nyckel.")


class AnonymizeRequest(BaseModel):
    sql: str = Field(..., max_length=MAX_SQL_CHARS)
    dialect: str = Field(
        "tsql",
        description=(
            "SQL-dialekt att använda vid parsning och generering. Standard: tsql. "
            "Vanliga val: tsql (SQL Server), postgres, mysql, bigquery, snowflake, "
            "redshift, databricks, spark, sqlite. "
            "Alla dialekter: athena, bigquery, clickhouse, databricks, doris, dremio, "
            "drill, druid, duckdb, dune, exasol, fabric, hive, materialize, mysql, "
            "oracle, postgres, presto, prql, redshift, risingwave, snowflake, solr, "
            "spark, spark2, sqlite, starrocks, tableau, teradata, trino, tsql."
        ),
    )


class AnonymizeResponse(BaseModel):
    sql: str
    mapping: dict[str, str]


class DeanonymizeRequest(BaseModel):
    text: str = Field(..., max_length=MAX_TEXT_CHARS)
    mapping: dict[str, str] = Field(..., max_length=MAX_MAPPING_ITEMS)


class DeanonymizeResponse(BaseModel):
    text: str


class ExplainRequest(BaseModel):
    sql: str = Field(..., max_length=MAX_SQL_CHARS)


class ExplainResponse(BaseModel):
    explanation: str


@app.post("/anonymize", response_model=AnonymizeResponse)
@limiter.limit("30/minute")
def anonymize_endpoint(req: AnonymizeRequest, request: Request) -> AnonymizeResponse:
    try:
        anonymized, mapping = anonymize_sql(req.sql, dialect=req.dialect)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return AnonymizeResponse(sql=anonymized, mapping=mapping)


@app.post("/deanonymize", response_model=DeanonymizeResponse)
@limiter.limit("30/minute")
def deanonymize_endpoint(req: DeanonymizeRequest, request: Request) -> DeanonymizeResponse:
    try:
        result = deanonymize_text(req.text, req.mapping)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return DeanonymizeResponse(text=result)


@app.post("/explain", response_model=ExplainResponse, dependencies=[Depends(verify_secret_key)])
@limiter.limit("10/minute")
def explain_endpoint(req: ExplainRequest, request: Request) -> ExplainResponse:
    try:
        api_key = get_api_key()
        client = anthropic.Anthropic(api_key=api_key)
        result = explain_sql(req.sql, client)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return ExplainResponse(explanation=result)
