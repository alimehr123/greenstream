# backend_services/layout_services/layout_runtime.py

"""
Layout Runtime
==============

This module is responsible for loading and validating UI layout definition
files (`*.layout.json`) before they are sent to the frontend.

Its responsibilities are intentionally limited and well-defined:

1. Load layout files from disk (I/O concern)
2. Validate layout structure against the official layout schema
   (`layout_schema.json`)
3. Fail fast if a layout is missing or structurally invalid

This service DOES NOT:
- Decide which layout should be used (that is ui_layout_resolver's job)
- Modify layout content
- Know anything about frontend implementation details

Architectural role:
-------------------
This file acts as the "gatekeeper" of the Layout Contract.
Any layout that successfully passes through this service is considered
safe and valid for frontend consumption.

If a layout breaks the schema, the error MUST be caught here,
not in the frontend.
"""

import json
from pathlib import Path

from jsonschema import validate, ValidationError

# ------------------------------------------------------------------
# Paths (single source of truth)
# ------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

LAYOUTS_DIR = BASE_DIR / "server" / "server_manager"/ "layout_editor" /"layouts"
SCHEMA_PATH = BASE_DIR / "server" / "contracts" / "layout_schema.json"


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def load_layout(layout_name: str) -> dict:
    """
    Load and validate a layout by name.

    Example:
        layout_name = "search_results"
        -> loads layouts/search_results.layout.json
    """

    layout_path = LAYOUTS_DIR / f"{layout_name}.layout.json"

    if not layout_path.exists():
        raise FileNotFoundError(f"Layout file not found: {layout_path}")

    # 1️⃣ Load layout JSON
    try:
        with layout_path.open("r", encoding="utf-8") as f:
            layout_data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in layout file: {layout_path}") from e

    # 2️⃣ Load schema
    try:
        with SCHEMA_PATH.open("r", encoding="utf-8") as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        raise RuntimeError("layout_schema.json is invalid") from e

    # 3️⃣ Validate layout against schema
    try:
        validate(instance=layout_data, schema=schema)
    except ValidationError as e:
        raise ValueError(
            f"Layout validation failed for '{layout_name}': {e.message}"
        ) from e

    # 4️⃣ Success → layout is safe to use
    return layout_data
