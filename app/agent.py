"""LangGraph + LangChain Text-to-SQL agent with dual self-correction.

                       +--------------+
   question ---------> | generate_sql |--(meta question)------------------------+
                       +------+-------+                                         |
                              v                                                 |
                       +--------------+   error & attempts<max   +-----------+  |
              +------->|   execute    |------------------------->| fix_syntax|  |
              |        +------+-------+                          +-----+-----+  |
              |               |  (loop: real, up to N)                  |        |
              +---------------+<----------------------------------------+        |
                              | success (phase=syntactic)                        |
                              v                                                  |
                       +----------------+  has_issue -> corrected SQL            |
                       |semantic_reflect|--(phase=semantic, ONE time)--> execute |
                       +------+---------+                                        |
                              | ok                                               |
                              v                                                  v
                          +----------------------- finalize <--------------------+
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

from . import config
from .db import execute_sql, format_result, get_schema_info
from .prompts import GENERATE_PROMPT, SEMANTIC_REFLECT_PROMPT, SYNTAX_FIX_PROMPT
from .routing import (AgentState, route_after_execute, route_after_generate,
                      route_after_reflect)
from .schemas import GenerationOutput, SemanticReviewOutput, SyntaxFixOutput


def _clean_sql(sql: str) -> str:
    """Strip markdown fences the model sometimes adds despite structured output."""
    s = (sql or "").strip()
    if s.startswith("```"):
        s = s.strip("`")
        if s.lower().startswith("sql"):
            s = s[3:]
    return s.strip().rstrip(";").strip() + ";" if s.strip() else ""


def _trace(state: AgentState, step: str, detail: str, sql: Optional[str] = None) -> List[Dict[str, Any]]:
    return list(state.get("trace", [])) + [{"step": step, "detail": detail, "sql": sql}]


def build_llm() -> ChatOpenAI:
    kwargs: Dict[str, Any] = {"model": config.LLM_MODEL, "temperature": config.LLM_TEMPERATURE}
    if config.LLM_BASE_URL:
        kwargs["base_url"] = config.LLM_BASE_URL
    return ChatOpenAI(**kwargs)


def build_graph(llm=None, schema: Optional[str] = None):
    """Compile the agent graph. ``llm`` can be any LangChain chat model (useful for tests)."""
    llm = llm or build_llm()
    schema_text = schema if schema is not None else get_schema_info()

    generate_chain = GENERATE_PROMPT | llm.with_structured_output(GenerationOutput)
    fix_chain = SYNTAX_FIX_PROMPT | llm.with_structured_output(SyntaxFixOutput)
    reflect_chain = SEMANTIC_REFLECT_PROMPT | llm.with_structured_output(SemanticReviewOutput)

    # ---- nodes -------------------------------------------------------------------------------
    def generate_sql(state: AgentState) -> Dict[str, Any]:
        out: GenerationOutput = generate_chain.invoke({"schema": schema_text, "question": state["question"]})
        if out.kind == "schema_answer" or not out.sql.strip():
            return {"status": "schema_answer", "answer": out.answer or "",
                    "trace": _trace(state, "generate", "Answered from the schema (no SQL needed).")}
        sql = _clean_sql(out.sql)
        return {"sql": sql, "trace": _trace(state, "generate", "Initial SQL generated.", sql)}

    def execute(state: AgentState) -> Dict[str, Any]:
        sql = state["sql"]
        result = execute_sql(sql)
        update: Dict[str, Any] = {"result": result}
        if state.get("phase") != "semantic":
            update["attempts"] = state.get("attempts", 0) + 1
        label = ("execute (semantic re-run)" if state.get("phase") == "semantic"
                 else f"execute (attempt {update['attempts']})")
        if result["status"] == "error":
            update["trace"] = _trace(state, label, f"DB error: {result['message']}", sql)
        else:
            update["trace"] = _trace(state, label, f"OK - {len(result['rows'])} row(s).", sql)
        return update

    def fix_syntax(state: AgentState) -> Dict[str, Any]:
        err = state["result"]["message"]
        history = list(state.get("failed_history", [])) + [f"{state['sql']}  -->  {err}"]
        out: SyntaxFixOutput = fix_chain.invoke({
            "schema": schema_text, "question": state["question"], "sql": state["sql"],
            "error": err, "history": "\n".join(history),
        })
        sql = _clean_sql(out.sql)
        return {"sql": sql, "failed_history": history,
                "trace": _trace(state, "syntactic_reflection", out.explanation or "Fixed SQL after DB error.", sql)}

    def semantic_reflect(state: AgentState) -> Dict[str, Any]:
        """ONE LLM call: diagnose + correct. Never loops."""
        review: SemanticReviewOutput = reflect_chain.invoke({
            "schema": schema_text, "question": state["question"],
            "sql": state["sql"], "result": format_result(state["result"]),
        })
        corrected = _clean_sql(review.corrected_sql or "")
        if review.has_issue and corrected and corrected.lower() != state["sql"].lower():
            return {"sql": corrected, "phase": "semantic", "semantic_applied": True,
                    "trace": _trace(state, "semantic_reflection",
                                    f"Logical issue found: {review.reasoning}", corrected)}
        return {"trace": _trace(state, "semantic_reflection",
                                f"Result accepted. {review.reasoning}".strip())}

    def finalize(state: AgentState) -> Dict[str, Any]:
        if state.get("status") == "schema_answer":
            return {}
        result = state["result"]
        if result["status"] == "error":
            if state.get("phase") == "semantic":
                msg = "The semantic correction produced a new database error; the agent stopped."
            else:
                msg = f"Could not produce an error-free query after {state['attempts']} attempt(s)."
            return {"status": "failed", "answer": f"{msg} Last error: {result['message']}",
                    "trace": _trace(state, "finalize", msg)}
        return {"status": "success", "trace": _trace(state, "finalize", "Result returned.")}

    # ---- graph -------------------------------------------------------------------------------
    g = StateGraph(AgentState)
    g.add_node("generate_sql", generate_sql)
    g.add_node("execute", execute)
    g.add_node("fix_syntax", fix_syntax)
    g.add_node("semantic_reflect", semantic_reflect)
    g.add_node("finalize", finalize)

    g.add_edge(START, "generate_sql")
    g.add_conditional_edges("generate_sql", route_after_generate,
                            {"execute": "execute", "finalize": "finalize"})
    g.add_conditional_edges("execute", route_after_execute,
                            {"fix_syntax": "fix_syntax", "semantic_reflect": "semantic_reflect",
                             "finalize": "finalize"})
    g.add_edge("fix_syntax", "execute")                       # <- the real loop
    g.add_conditional_edges("semantic_reflect", route_after_reflect,
                            {"execute": "execute", "finalize": "finalize"})  # one-shot, forward only
    g.add_edge("finalize", END)
    return g.compile()


def run_agent(graph, question: str, max_attempts: Optional[int] = None) -> Dict[str, Any]:
    initial: AgentState = {
        "question": question, "phase": "syntactic", "attempts": 0,
        "max_attempts": max_attempts or config.MAX_SYNTACTIC_ATTEMPTS,
        "failed_history": [], "semantic_applied": False, "trace": [],
    }
    # recursion_limit is a hard safety net; the routing already bounds the loops.
    return graph.invoke(initial, config={"recursion_limit": 25})
