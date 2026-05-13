import anthropic
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from sql_anon.anonymize import anonymize as anonymize_sql
from sql_anon.config import get_api_key
from sql_anon.deanonymize import deanonymize as deanonymize_text
from sql_anon.explain import explain as explain_sql

# Storleksgränser på request-payload. Pydantic returnerar 422 automatiskt om de
# överskrids — håller bort DoS och oavsiktlig credit-dränering på /explain.
MAX_SQL_CHARS = 100_000
MAX_TEXT_CHARS = 100_000
MAX_MAPPING_ITEMS = 10_000


class AnonymizeRequest(BaseModel):
    sql: str = Field(..., max_length=MAX_SQL_CHARS)


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


app = FastAPI(
    title="sql-anon",
    description="API för att förklara, anonymisera och avanonymisera SQL.",
)


@app.post("/anonymize", response_model=AnonymizeResponse)
def anonymize_endpoint(req: AnonymizeRequest) -> AnonymizeResponse:
    try:
        anonymized, mapping = anonymize_sql(req.sql)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return AnonymizeResponse(sql=anonymized, mapping=mapping)


@app.post("/deanonymize", response_model=DeanonymizeResponse)
def deanonymize_endpoint(req: DeanonymizeRequest) -> DeanonymizeResponse:
    try:
        result = deanonymize_text(req.text, req.mapping)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return DeanonymizeResponse(text=result)


@app.post("/explain", response_model=ExplainResponse)
def explain_endpoint(req: ExplainRequest) -> ExplainResponse:
    try:
        api_key = get_api_key()
        client = anthropic.Anthropic(api_key=api_key)
        result = explain_sql(req.sql, client)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    return ExplainResponse(explanation=result)
