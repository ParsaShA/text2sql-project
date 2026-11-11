"""Pure-Python state + routing logic of the graph (no LLM / framework imports -> unit-testable).

Two reflection policies, deliberately different:

* SYNTACTIC reflection  - real LOOP. Feedback is the DB engine's error (deterministic), so we can
  retry up to ``max_syntactic_attempts`` times.
* SEMANTIC reflection   - ONE-SHOT, forward only. A single LLM call both diagnoses the logical problem
  and returns the corrected SQL; the corrected SQL is executed once and the flow goes to the output.
  The ``phase`` flag makes a second semantic pass structurally impossible.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class AgentState(TypedDict, total=False):
    question: str
    schema: str
    sql: str
    result: Dict[str, Any]
    phase: str                    # "syntactic" | "semantic"
    attempts: int                 # syntactic executions so far
    max_attempts: int
    failed_history: List[str]     # earlier failing SQL + error, shown to the fixer
    semantic_applied: bool
    status: str                   # success | schema_answer | failed
    answer: Optional[str]
    trace: List[Dict[str, Any]]


def route_after_generate(state: AgentState) -> str:
    return "finalize" if state.get("status") == "schema_answer" else "execute"


def route_after_execute(state: AgentState) -> str:
    result = state["result"]
    if result["status"] == "error":
        # An error after the one-shot semantic correction ends the run (no further loops).
        if state.get("phase") == "semantic":
            return "finalize"
        if state["attempts"] >= state["max_attempts"]:
            return "finalize"
        return "fix_syntax"               # <-- the real loop
    # success
    if state.get("phase") == "semantic":
        return "finalize"                 # corrected query ran fine -> output, no more reflection
    return "semantic_reflect"             # first successful execution -> one-shot semantic review


def route_after_reflect(state: AgentState) -> str:
    # reflect node sets phase="semantic" only when it produced a corrected query
    return "execute" if state.get("phase") == "semantic" else "finalize"
