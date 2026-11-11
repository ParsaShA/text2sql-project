"""Central configuration, read from environment variables (.env supported)."""
import os
from pathlib import Path

try:  # optional: load .env if python-dotenv is installed
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("DB_PATH", BASE_DIR / "bank_database.db"))

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_BASE_URL = os.getenv("LLM_BASE_URL") or None   # any OpenAI-compatible endpoint
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))

MAX_SYNTACTIC_ATTEMPTS = int(os.getenv("MAX_SYNTACTIC_ATTEMPTS", "3"))
MAX_ROWS = int(os.getenv("MAX_ROWS", "100"))
