# server/services/backend_services/state_aggregation/ui_state_aggregator.py

"""
UI State Aggregator
==================

ROLE (LOCKED):
--------------
Aggregates decision results produced by Capabilities
into a single, UI-ready State object that fully conforms
to the Layout Contract (State – CORE CONTRACT).

This module is the ONLY place where:
- Capability outputs are merged into State
- Ownership and lifecycle are respected as declared
- Conflicting state keys are detected as architecture errors

This module does NOT:
- Make decisions
- Infer missing state
- Provide defaults
- Interpret layout or components
- Validate full JSON schema (that is a separate concern)

Architectural Position:
------------------------
Capability Execution
    └── decision results (semantic, resolved)
State Aggregator (THIS MODULE)
    └── assembles declarative State
UI Response Finalizer
    └── enforces response contract and freezes output
"""

from typing import Dict, Any, Iterable


# -------------------------------
# Public API (LOCKED)
# -------------------------------

def aggregate_ui_state(
    *,
    capability_results: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Aggregates State fragments from multiple Capability results.

    INPUT CONTRACT:
    ----------------
    capability_results:
        An iterable of Capability outputs.

        Each capability output MAY include:
        {
            "state": {
                "<state_key>": <State Definition Object>
            }
        }

        - Capabilities MUST NOT overlap on state ownership
        - State definitions MUST already be decision-resolved
        - This function assumes Capabilities are contract-faithful

    OUTPUT CONTRACT:
    -----------------
    Returns a SINGLE State object:

    {
        "<state_key>": {
            "owner": "layout" | "page" | "component",
            "type": "...",
            "lifecycle": {...},
            "initial": <UI-ready value>,
            ...
        }
    }

    The output is suitable for direct consumption by:
    - Layout renderer
    - UI Response Finalizer
    """

    aggregated_state: Dict[str, Any] = {}

    for result in capability_results:
        _merge_capability_state(
            aggregated_state=aggregated_state,
            capability_result=result,
        )

    return aggregated_state


# -------------------------------
# Internal Merge Logic (LOCKED)
# -------------------------------

def _merge_capability_state(
    *,
    aggregated_state: Dict[str, Any],
    capability_result: Dict[str, Any],
) -> None:
    """
    Merges the 'state' section of a single Capability result
    into the aggregated state container.

    Conflict Rules (LOCKED):
    ------------------------
    - A state key may be declared ONCE globally
    - Duplicate keys are a SYSTEM ERROR
    - No overwriting or reconciliation is allowed
    """

    state_fragment = capability_result.get("state")

    if not state_fragment:
        return

    if not isinstance(state_fragment, dict):
        raise ValueError(
            "Invalid Capability Result: 'state' must be a dictionary."
        )

    for state_key, state_definition in state_fragment.items():
        _assert_state_key_is_new(
            aggregated_state=aggregated_state,
            state_key=state_key,
        )

        _assert_state_definition_is_valid_shape(state_key, state_definition)

        aggregated_state[state_key] = state_definition


# -------------------------------
# Assertions (SHAPE-LEVEL ONLY)
# -------------------------------

def _assert_state_key_is_new(
    *,
    aggregated_state: Dict[str, Any],
    state_key: str,
) -> None:
    """
    Ensures no two Capabilities attempt to own the same state key.

    Ownership conflicts are NOT resolvable automatically
    and represent a broken Capability Map.
    """
    if state_key in aggregated_state:
        raise ValueError(
            f"State Aggregation Error: duplicate state key '{state_key}'. "
            "Multiple Capabilities are attempting to define the same State."
        )


def _assert_state_definition_is_valid_shape(
    state_key: str,
    state_definition: Any,
) -> None:
    """
    Performs minimal, defensive checks on the state definition.

    IMPORTANT:
    ----------
    - This is NOT full schema validation
    - This does NOT check business meaning
    - This does NOT apply defaults

    It only ensures that the object looks like
    a Layout Contract State Definition.
    """

    if not isinstance(state_definition, dict):
        raise ValueError(
            f"Invalid State Definition for '{state_key}': "
            "state definition must be a dictionary."
        )

    required_fields = {"owner", "type", "lifecycle"}

    missing = required_fields - state_definition.keys()
    if missing:
        raise ValueError(
            f"Invalid State Definition for '{state_key}': "
            f"missing required fields: {sorted(missing)}"
        )

    lifecycle = state_definition.get("lifecycle")
    if not isinstance(lifecycle, dict):
        raise ValueError(
            f"Invalid State Definition for '{state_key}': "
            "'lifecycle' must be a dictionary."
        )

    if "create" not in lifecycle or "destroy" not in lifecycle:
        raise ValueError(
            f"Invalid State Definition for '{state_key}': "
            "'lifecycle' must define 'create' and 'destroy'."
        )
