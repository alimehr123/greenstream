# backend_services/layout_services/layout_loader.py

"""
Layout Loader (LOCKED ✅)

ROLE:
-----
Responsible for loading and validating raw Layout JSON files.

Responsibilities:
- Load declarative layout schema by name
- Validate against the LOCKED Layout Contract
- Fail fast on missing or invalid layouts

This module MUST NOT:
- Interpret layout semantics
- Compile layouts
- Build or mutate state
- Inspect request context
- Execute actions or capabilities
"""

import json
from pathlib import Path
from typing import Dict, Any

from jsonschema import validate, ValidationError

# --------------------------------------------------
# Layout storage configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
LAYOUT_DIR = (
    BASE_DIR
    / "server_manager"
    / "layout_editor"
    / "layouts"
)

# --------------------------------------------------
# Layout Contract Schema (LOCKED)
# --------------------------------------------------

LAYOUT_CONTRACT_PATH = BASE_DIR / "architecture" / "layout_schema.json"

def _load_layout_contract_schema() -> Dict[str, Any]:
    if not LAYOUT_CONTRACT_PATH.exists():
        raise RuntimeError(
            f"Layout contract schema not found: {LAYOUT_CONTRACT_PATH}"
        )

    with open(LAYOUT_CONTRACT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


_LAYOUT_CONTRACT_SCHEMA = _load_layout_contract_schema()

# --------------------------------------------------
# Public API
# --------------------------------------------------

def load_layout(layout_name: str) -> Dict[str, Any]:
    """
    Load and validate a raw declarative layout schema.

    Args:
        layout_name: Logical layout identifier (without extension)

    Returns:
        Raw layout JSON (validated, uncompiled)

    Raises:
        FileNotFoundError: Layout file not found
        ValueError: Invalid layout schema
    """

    layout_path = LAYOUT_DIR / f"{layout_name}.json"

    if not layout_path.exists():
        raise FileNotFoundError(
            f"Layout file not found: {layout_path}"
        )

    try:
        with open(layout_path, "r", encoding="utf-8") as f:
            layout_schema = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Invalid JSON in layout '{layout_name}': {e}"
        )

    try:
        validate(
            instance=layout_schema,
            schema=_LAYOUT_CONTRACT_SCHEMA,
        )
    except ValidationError as e:
        raise ValueError(
            f"Layout '{layout_name}' violates Layout Contract: {e.message}"
        )

    return layout_schema
