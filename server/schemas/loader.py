# server/schemas/loader.py

import json
from pathlib import Path

SCHEMA_DIR = Path(__file__).parent


def load_json_schema(filename: str) -> dict:
    path = SCHEMA_DIR / filename
    if not path.exists():
        raise RuntimeError(f"Schema not found: {filename}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
