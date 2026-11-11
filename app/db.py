"""Database layer.

* LangChain's ``SQLDatabase`` produces the schema description (DDL + sample rows)
  that goes into the prompts.
* Execution uses a *read-only* sqlite3 connection, so the agent can never modify data,
  plus an explicit statement guard (defence in depth).
* ``execute_sql`` never raises: it returns a dict so the graph can route on
  ``status == "error"`` (this is the *syntactic* feedback signal).
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional

from . import config

_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|replace|truncate|attach|detach|pragma|vacuum|reindex)\b",
    re.IGNORECASE,
)


def get_schema_info(db_path: Optional[Path] = None) -> str:
    """Schema text for prompts, produced by LangChain's SQLDatabase tool."""
    from langchain_community.utilities import SQLDatabase  # imported lazily

    path = Path(db_path or config.DB_PATH)
    db = SQLDatabase.from_uri(f"sqlite:///{path}", sample_rows_in_table_info=2)
    return db.get_table_info()


def _strip_comments(sql: str) -> str:
    sql = re.sub(r"--[^\n]*", " ", sql)
    return re.sub(r"/\*.*?\*/", " ", sql, flags=re.S).strip()


def validate_read_only(sql: str) -> Optional[str]:
    """Return an error message if the statement is not a single read-only SELECT, else None."""
    cleaned = _strip_comments(sql or "").rstrip(";").strip()
    if not cleaned:
        return "Empty SQL statement."
    no_literals = re.sub(r"'(?:[^']|'')*'", "''", cleaned)
    if ";" in no_literals:
        return "Only a single SQL statement is allowed."
    if not re.match(r"^(select|with)\b", cleaned, re.IGNORECASE):
        return "Only read-only SELECT queries are allowed."
    hit = _FORBIDDEN.search(no_literals)
    if hit:
        return f"Forbidden keyword in query: {hit.group(0).upper()}"
    return None


def execute_sql(sql: str, db_path: Optional[Path] = None, max_rows: Optional[int] = None) -> Dict[str, Any]:
    """Run ``sql`` and return {status, columns, rows, message}. Never raises."""
    path = Path(db_path or config.DB_PATH)
    limit = max_rows or config.MAX_ROWS

    problem = validate_read_only(sql)
    if problem:
        return {"status": "error", "columns": [], "rows": [], "message": problem}

    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            cur = conn.execute(sql)
            columns = [d[0] for d in cur.description] if cur.description else []
            rows = [list(r) for r in cur.fetchmany(limit)]
        finally:
            conn.close()
        return {"status": "success", "columns": columns, "rows": rows, "message": ""}
    except sqlite3.Error as exc:  # OperationalError: no such column, syntax error, ...
        return {"status": "error", "columns": [], "rows": [], "message": f"{type(exc).__name__}: {exc}"}


def format_result(result: Dict[str, Any], max_preview: int = 20) -> str:
    """Compact text rendering of a result, used when feeding results back to the LLM."""
    if result["status"] == "error":
        return f"ERROR: {result['message']}"
    if not result["rows"]:
        return f"columns={result['columns']}  rows=[]  (EMPTY RESULT)"
    shown = result["rows"][:max_preview]
    more = "" if len(result["rows"]) <= max_preview else f" ... (+{len(result['rows']) - max_preview} more)"
    return f"columns={result['columns']}\nrows={shown}{more}"
