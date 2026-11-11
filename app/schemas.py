"""Pydantic models: structured LLM outputs and the FastAPI request/response contract."""
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field


# ---- structured outputs the LLM must return -------------------------------------------------
class GenerationOutput(BaseModel):
    kind: Literal["sql", "schema_answer"] = Field(description="'sql' for data questions, 'schema_answer' for meta questions")
    sql: str = Field(default="", description="A single SQLite SELECT statement (empty for schema_answer)")
    answer: str = Field(default="", description="Natural-language answer for schema_answer questions")


class SyntaxFixOutput(BaseModel):
    sql: str = Field(description="Corrected single SQLite SELECT statement")
    explanation: str = Field(default="", description="One sentence: what was wrong")


class SemanticReviewOutput(BaseModel):
    """ONE call = diagnosis + correction (no separate fixer step/model)."""
    has_issue: bool
    reasoning: str = Field(default="", description="Why the result is (not) logically correct")
    corrected_sql: Optional[str] = Field(default=None, description="Corrected SELECT if has_issue, else null")


# ---- API ---------------------------------------------------------------------------------------
class QueryRequest(BaseModel):
    question: str = Field(min_length=2, examples=["مجموع مبالغ انتقال وجه از حساب ACC100001 چقدر است؟"])
    max_syntactic_attempts: Optional[int] = Field(default=None, ge=1, le=6)


class TraceStep(BaseModel):
    step: str
    detail: str
    sql: Optional[str] = None


class QueryResponse(BaseModel):
    status: Literal["success", "schema_answer", "failed"]
    question: str
    answer: Optional[str] = None
    sql: Optional[str] = None
    columns: List[str] = []
    rows: List[List[Any]] = []
    syntactic_attempts: int = 0
    semantic_correction_applied: bool = False
    trace: List[TraceStep] = []
