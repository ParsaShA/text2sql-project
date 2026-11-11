# Text-to-SQL Agent with Dual Self-Correction

**Stack:** LangChain (prompts, structured output, `SQLDatabase` schema tool) · LangGraph (agent graph) · FastAPI (service).

## Run
```bash
pip install -r requirements.txt
cp .env.example .env            # add OPENAI_API_KEY
python create_table.py          # creates bank_database.db
uvicorn app.main:app --reload   # UI: http://127.0.0.1:8000  ·  API docs: /docs
python evaluate.py              # runs the 10 evaluation questions against gold SQL
python -m unittest -v           # offline tests (no LLM needed)
```

```bash
curl -X POST localhost:8000/query -H 'Content-Type: application/json' \
  -d '{"question": "مجموع مبالغ انتقال وجه از حساب مبدأ ACC100001 چقدر است؟"}'
```

## How the two reflection paths differ (as required by the brief)
| | Syntactic reflection | Semantic reflection |
|---|---|---|
| Signal | DB engine error (deterministic) | Result vs. question (LLM judgement) |
| Shape | **Real loop**, up to `MAX_SYNTACTIC_ATTEMPTS` (default 3) | **One-shot, forward only** |
| LLM calls | 1 per retry (`fix_syntax`) | **1 total**: diagnoses *and* returns corrected SQL |
| After it | back to `execute` | corrected SQL is executed once → output |

The one-shot guarantee is structural: `semantic_reflect` is reachable only while `phase == "syntactic"`;
it flips `phase` to `"semantic"`, and `route_after_execute` sends every outcome in that phase to `finalize`.
If the corrected query errors, the agent stops (it does not re-enter the loop).

## Layout
```
create_table.py      DB bootstrap (from the brief)
app/db.py            read-only execution + SELECT-only guard + LangChain SQLDatabase schema
app/prompts.py       engineered prompts (DDL + domain notes, e.g. Transfer uses integer IDs)
app/routing.py       pure routing logic (unit-tested without any framework)
app/agent.py         LangGraph graph: generate → execute ⇄ fix_syntax → semantic_reflect → finalize
app/main.py          FastAPI: POST /query, GET /schema, GET /health, GET / (demo UI)
tests/               offline tests + the 10 evaluation questions with gold SQL
evaluate.py          scores the live agent against gold results
```
