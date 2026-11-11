"""Run the evaluation set against the live agent and compare to gold results.

    python evaluate.py            # needs OPENAI_API_KEY (or LLM_BASE_URL + key)
"""
import sys

from app.agent import build_graph, run_agent
from app.db import execute_sql
from tests.eval_questions import EVAL_SET


def _norm(rows, ordered=False):
    r = [tuple(round(v, 2) if isinstance(v, float) else v for v in row) for row in rows]
    return r if ordered else sorted(r, key=repr)


def main() -> int:
    graph = build_graph()
    passed = 0
    for item in EVAL_SET:
        final = run_agent(graph, item["question"])
        if item["gold_sql"] is None:
            ok = final.get("status") == "schema_answer"
        else:
            gold = execute_sql(item["gold_sql"])
            got = final.get("result", {"rows": []}) if final.get("status") == "success" else {"rows": []}
            ok = (final.get("status") == "success" and
                  _norm(got["rows"], item.get("ordered")) == _norm(gold["rows"], item.get("ordered")))
        passed += ok
        print(f"[{'PASS' if ok else 'FAIL'}] #{item['id']:>2} ({item['level']:<10}) "
              f"syntactic_attempts={final.get('attempts', 0)} "
              f"semantic_fix={final.get('semantic_applied', False)}")
        if not ok:
            print("      SQL:", final.get("sql"))
    print(f"\n{passed}/{len(EVAL_SET)} passed")
    return 0 if passed == len(EVAL_SET) else 1


if __name__ == "__main__":
    sys.exit(main())
