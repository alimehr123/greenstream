# backend_services/state_aggregation/ui_state_aggregator.py

from typing import Dict, Any, List
from copy import deepcopy

# ✅ NEW: State Schema Registry enforcement
from backend_services.state_aggregation.state_schema_registry import (
    validate_state_patch,
)
from backend_services.state_aggregation.errors import StateSchemaError


class UIStateAggregationError(Exception):
    """Raised when state aggregation violates contract rules."""


def aggregate_ui_state(
    *,
    base_state: Dict[str, Any],
    capability_results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Aggregate UI state patches emitted by Capabilities into a single UI State.

    Responsibilities (LOCKED):
    - Merge semantic state patches
    - Enforce explicit ownership
    - Prevent undeclared or conflicting state writes
    - Produce UI-ready, contract-safe State

    Output:
    - Aggregated `state` dict ONLY (no navigation, no metadata)
    """

    if not isinstance(base_state, dict):
        raise UIStateAggregationError("base_state must be a dict")

    aggregated_state: Dict[str, Any] = deepcopy(base_state)

    for capability_result in capability_results:
        if not capability_result:
            continue

        state_patches = capability_result.get("state_patches", [])
        if not state_patches:
            continue

        if not isinstance(state_patches, list):
            raise UIStateAggregationError("state_patches must be a list")

        for patch in state_patches:
            _apply_state_patch(
                aggregated_state=aggregated_state,
                patch=patch,
            )

    return aggregated_state


# ---------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------

def _apply_state_patch(
    *,
    aggregated_state: Dict[str, Any],
    patch: Dict[str, Any],
) -> None:
    """
    Apply a single state patch to the aggregated state with full validation.
    """

    if not isinstance(patch, dict):
        raise UIStateAggregationError("State patch must be an object")

    # ✅ HARD CONTRACT ENFORCEMENT (Registry is the authority)
    try:
        validate_state_patch(patch)
    except StateSchemaError as e:
        raise UIStateAggregationError(str(e)) from e

    target = patch["target"]
    data = patch.get("data")
    owner = patch["owner"]
    lifecycle = patch["lifecycle"]

    # ✅ Single-writer rule (still Aggregator responsibility)
    if target in aggregated_state:
        raise UIStateAggregationError(
            f"State '{target}' already defined — multiple writers are forbidden"
        )

    aggregated_state[target] = {
        "owner": owner,
        "type": _infer_state_type(data),
        "lifecycle": lifecycle,
        "initial": data,
    }

    # Scope metadata (already validated by registry)
    if owner == "page":
        aggregated_state[target]["page"] = patch.get("page")
    elif owner == "component":
        aggregated_state[target]["component"] = patch.get("component")


def _infer_state_type(value: Any) -> str:
    if value is None:
        return "object"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"

    raise UIStateAggregationError(
        f"Unsupported state value type: {type(value)}"
    )
