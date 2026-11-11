"""Offline tests (no LLM, no network, no langchain needed):  python -m unittest -v"""
import unittest

from app.db import execute_sql, validate_read_only
from app.routing import route_after_execute, route_after_reflect, route_after_generate
from tests.eval_questions import EVAL_SET


class TestGuard(unittest.TestCase):
    def test_allows_select_and_cte(self):
        self.assertIsNone(validate_read_only("SELECT 1;"))
        self.assertIsNone(validate_read_only("WITH x AS (SELECT 1) SELECT * FROM x"))

    def test_blocks_writes(self):
        for bad in ["DROP TABLE Customer", "DELETE FROM Account", "UPDATE Account SET Balance=0",
                    "SELECT 1; DROP TABLE Customer", "PRAGMA table_info(Account)", "INSERT INTO Customer VALUES (1)"]:
            self.assertIsNotNone(validate_read_only(bad), bad)

    def test_keyword_inside_string_literal_is_fine(self):
        self.assertIsNone(validate_read_only("SELECT * FROM Account WHERE Status = 'delete'"))

    def test_db_is_physically_read_only(self):
        r = execute_sql("SELECT * FROM Customer")
        self.assertEqual(r["status"], "success")


class TestDatabaseSignals(unittest.TestCase):
    def test_syntactic_error_is_reported_not_raised(self):
        r = execute_sql("SELECT UserFirstName FROM Customer")
        self.assertEqual(r["status"], "error")
        self.assertIn("no such column", r["message"])

    def test_semantic_scenario_runs_but_is_wrong(self):
        naive = execute_sql("SELECT SUM(Amount) FROM Transfer WHERE FromAccountID = 'ACC100001';")
        self.assertEqual(naive["status"], "success")
        self.assertEqual(naive["rows"], [[None]])             # silent logical bug
        good = execute_sql(next(i for i in EVAL_SET if i["id"] == 10)["gold_sql"])
        self.assertAlmostEqual(good["rows"][0][0], 1435.18 + 1820.68 + 666.55, places=2)

    def test_all_gold_queries_execute_and_return_rows(self):
        for item in EVAL_SET:
            if item["gold_sql"]:
                r = execute_sql(item["gold_sql"])
                self.assertEqual(r["status"], "success", item["id"])
                self.assertTrue(r["rows"], f"gold #{item['id']} returned no rows")


def simulate(first_sql_results, semantic_has_issue, corrected_result=None, max_attempts=3):
    """Drive the real routing functions with scripted execution results; return the node path."""
    state = {"phase": "syntactic", "attempts": 0, "max_attempts": max_attempts}
    path, node = ["generate_sql"], "execute"
    results, corr = list(first_sql_results), corrected_result
    while node != "finalize":
        path.append(node)
        if node == "execute":
            if state["phase"] != "semantic":
                state["attempts"] += 1
                state["result"] = results.pop(0)
            else:
                state["result"] = corr
            node = route_after_execute(state)
        elif node == "fix_syntax":
            node = "execute"
        elif node == "semantic_reflect":
            if semantic_has_issue:
                state["phase"] = "semantic"
            node = route_after_reflect(state)
    path.append("finalize")
    return path, state


OK, ERR = {"status": "success"}, {"status": "error", "message": "boom"}


class TestRouting(unittest.TestCase):
    def test_meta_question_skips_db(self):
        self.assertEqual(route_after_generate({"status": "schema_answer"}), "finalize")

    def test_happy_path_one_reflection_no_fix(self):
        path, st = simulate([OK], semantic_has_issue=False)
        self.assertEqual(path, ["generate_sql", "execute", "semantic_reflect", "finalize"])

    def test_syntactic_loop_repeats_then_succeeds(self):
        path, st = simulate([ERR, ERR, OK], semantic_has_issue=False)
        self.assertEqual(path.count("fix_syntax"), 2)
        self.assertEqual(st["attempts"], 3)

    def test_syntactic_loop_is_bounded(self):
        path, st = simulate([ERR, ERR, ERR], semantic_has_issue=False, max_attempts=3)
        self.assertEqual(path.count("fix_syntax"), 2)
        self.assertNotIn("semantic_reflect", path)

    def test_semantic_is_one_shot_forward(self):
        path, st = simulate([OK], semantic_has_issue=True, corrected_result=OK)
        self.assertEqual(path.count("semantic_reflect"), 1)        # exactly once, never a loop
        self.assertEqual(path, ["generate_sql", "execute", "semantic_reflect", "execute", "finalize"])

    def test_error_after_semantic_correction_stops(self):
        path, st = simulate([OK], semantic_has_issue=True, corrected_result=ERR)
        self.assertNotIn("fix_syntax", path)                       # no re-entering the loop
        self.assertEqual(path[-1], "finalize")


if __name__ == "__main__":
    unittest.main()
