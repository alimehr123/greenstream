# server/services/ui_response_finalizer.py

"""
UI Response Finalizer
====================

ROLE (LOCKED):
--------------
This module is the FINAL boundary between Backend and Frontend.

It does NOT:
- Make decisions
- Build or merge state
- Interpret layout or state
- Apply business logic

It ONLY:
- Enforces the Backend → Frontend Response Contract
- Attaches response-level metadata
- Freezes the response payload before it leaves the backend

Architectural Position:
------------------------
State Aggregator
    └── produces aggregated, UI-ready state (DECISIONS DONE)
Layout Compiler
    └── produces compiled render tree (STRUCTURE ONLY)
Actions Resolver
    └── produces resolved, semantic actions

UI Response Finalizer (THIS MODULE)
    └── validates presence + shape
    └── enforces response contract
    └── adds metadata (build_id, schema_version)
    └── outputs immutable response payload
"""

from typing import Dict, Any
from uuid import uuid4
from datetime import datetime


# -------------------------------
# Public API (LOCKED)
# -------------------------------

def finalize_ui_response(
    *,
    layout: Dict[str, Any],
    state: Dict[str, Any],
    actions: Dict[str, Any] | None = None,
    schema_version: str = "1.0"
) -> Dict[str, Any]:
    """
    Finalizes the UI response payload.

    INPUT CONTRACT:
    ----------------
    layout:
        - Compiled layout tree
        - Pure structure
        - Must already conform to Layout Contract
        - Must NOT contain decisions

    state:
        - Fully aggregated, UI-ready State
        - Produced by State Aggregation layer
        - Must represent resolved decisions only
        - Must conform to Layout Contract's "State (CORE CONTRACT)"

    actions:
        - Resolved, semantic actions
        - No UI-specific targets or structural references
        - Optional (defaults to empty)

    OUTPUT CONTRACT:
    -----------------
    Returns the FINAL response object sent to the UI.

    Shape (LOCKED):

    {
        "layout": {...},
        "state": {...},
        "actions": {...},
        "meta": {
            "build_id": "...",
            "schema_version": "...",
            "generated_at": "ISO-8601 UTC"
        }
    }

    After this function:
    --------------------
    - No mutation is allowed
    - No decisions are allowed
    - No inference is allowed
    """

    _assert_layout_present(layout)
    _assert_state_present(state)
    
    if actions is not None and not isinstance(actions, dict):
        raise ValueError("actions must be a dictionary if provided")

    response = {
        "layout": layout,
        "state": state,
        "actions": actions or {},
        "meta": {
            "build_id": _generate_build_id(),
            "schema_version": schema_version,
            "generated_at": _utc_now_iso(),
        },
    }

    return response


# -------------------------------
# Internal Assertions (LOCKED)
# -------------------------------

def _assert_layout_present(layout: Dict[str, Any]) -> None:
    """
    Ensures layout exists.

    This function does NOT validate layout content.
    Layout semantic correctness is enforced earlier by:
    - Layout compiler
    - Layout schema validator

    Responsibility here:
    - Boundary-level presence assertion ONLY
    """
    if not isinstance(layout, dict) or not layout:
        raise ValueError(
            "UI Response Finalization Failed: "
            "layout must be a non-empty dictionary."
        )


def _assert_state_present(state: Dict[str, Any]) -> None:
    """
    Ensures state exists and is not empty.

    IMPORTANT:
    ----------
    - This does NOT build state
    - This does NOT merge state
    - This does NOT infer defaults

    If state is missing here, it is a SYSTEM ARCHITECTURE ERROR,
    not a recoverable condition.
    """
    if not isinstance(state, dict):
        raise ValueError(
            "UI Response Finalization Failed: "
            "state must be a dictionary."
        )

    if not state:
        raise ValueError(
            "UI Response Finalization Failed: "
            "state is empty. State Aggregation layer is missing or failed."
        )


# -------------------------------
# Utilities (Pure / Deterministic)
# -------------------------------

def _generate_build_id() -> str:
    """
    Generates a unique build identifier for the UI response.

    Used for:
    - Debugging
    - Traceability
    - Client-side reconciliation

    NOT used for:
    - Decisions
    - Caching logic
    """
    return uuid4().hex


def _utc_now_iso() -> str:
    """
    Returns current UTC time in ISO-8601 format.
    """
    return datetime.utcnow().isoformat() + "Z"
