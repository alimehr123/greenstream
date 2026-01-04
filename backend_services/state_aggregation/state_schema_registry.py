# backend_services/state_aggregation/state_schema_registry.py

from typing import Dict, Any, Iterable

from backend_services.state_aggregation.errors import (
    UnknownStateTargetError,
    InvalidStateOwnerError,
    InvalidStateLifecycleError,
    InvalidStateDataError,
)

from backend_services.state_aggregation.schemas.video_player import (
    STATE_SCHEMA as VIDEO_PLAYER_SCHEMA,
)
from backend_services.state_aggregation.schemas.search_results import (
    STATE_SCHEMA as SEARCH_RESULTS_SCHEMA,
)


# ✅ Central registry (LOCKED entry point)
_STATE_SCHEMAS = {
    VIDEO_PLAYER_SCHEMA["target"]: VIDEO_PLAYER_SCHEMA,
    SEARCH_RESULTS_SCHEMA["target"]: SEARCH_RESULTS_SCHEMA,
}


def get_state_schema(target: str) -> Dict[str, Any]:
    schema = _STATE_SCHEMAS.get(target)

    if not schema:
        raise UnknownStateTargetError(
            f"No State Schema registered for target '{target}'"
        )

    return schema


def validate_state_patch(patch: Dict[str, Any]) -> None:
    """
    Enforces HARD State Contract.

    Expected patch shape (semantic, not UI):
    {
        target,
        owner,
        page? | component?,
        lifecycle,
        data
    }
    """

    if not isinstance(patch, dict):
        raise InvalidStateDataError("State patch must be an object")

    target = patch.get("target")
    schema = get_state_schema(target)

    # ------------------------------------------------------------------
    # Owner enforcement
    # ------------------------------------------------------------------
    if patch.get("owner") != schema["owner"]:
        raise InvalidStateOwnerError(
            f"Invalid owner for state '{target}': "
            f"{patch.get('owner')} (expected {schema['owner']})"
        )

    # ------------------------------------------------------------------
    # Scope enforcement (page / component)
    # ------------------------------------------------------------------
    if schema["owner"] == "page":
        if patch.get("page") != schema.get("page"):
            raise InvalidStateOwnerError(
                f"Invalid page scope for state '{target}': "
                f"{patch.get('page')} (expected {schema.get('page')})"
            )

    if schema["owner"] == "component":
        if patch.get("component") != schema.get("component"):
            raise InvalidStateOwnerError(
                f"Invalid component scope for state '{target}': "
                f"{patch.get('component')} (expected {schema.get('component')})"
            )

    # ------------------------------------------------------------------
    # Lifecycle enforcement
    # ------------------------------------------------------------------
    lifecycle = patch.get("lifecycle")
    expected_lifecycle = schema["lifecycle"]

    if not isinstance(lifecycle, dict):
        raise InvalidStateLifecycleError(
            f"State '{target}' lifecycle must be an object"
        )

    if lifecycle.get("create") != expected_lifecycle["create"]:
        raise InvalidStateLifecycleError(
            f"Invalid lifecycle.create for '{target}' "
            f"(expected {expected_lifecycle['create']})"
        )

    if lifecycle.get("destroy") != expected_lifecycle["destroy"]:
        raise InvalidStateLifecycleError(
            f"Invalid lifecycle.destroy for '{target}' "
            f"(expected {expected_lifecycle['destroy']})"
        )

    # ------------------------------------------------------------------
    # Data validation (schema-driven)
    # ------------------------------------------------------------------
    data = patch.get("data")
    expected_type = schema["type"]

    if expected_type == "object":
        _validate_object_data(target, data, schema)

    elif expected_type == "array":
        _validate_array_data(target, data, schema)

    else:
        raise InvalidStateDataError(
            f"Unsupported state type '{expected_type}' for '{target}'"
        )


# =====================================================================
# Internal helpers (LOCKED responsibilities)
# =====================================================================

def _validate_object_data(
    target: str,
    data: Any,
    schema: Dict[str, Any],
) -> None:
    if not isinstance(data, dict):
        raise InvalidStateDataError(
            f"State '{target}' data must be an object"
        )

    for field in schema.get("required_fields", []):
        if field not in data:
            raise InvalidStateDataError(
                f"Missing required field '{field}' in state '{target}'"
            )


def _validate_array_data(
    target: str,
    data: Any,
    schema: Dict[str, Any],
) -> None:
    if not isinstance(data, list):
        raise InvalidStateDataError(
            f"State '{target}' data must be an array"
        )

    required_fields = schema.get("required_fields", [])

    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise InvalidStateDataError(
                f"Item #{index} in state '{target}' must be an object"
            )

        for field in required_fields:
            if field not in item:
                raise InvalidStateDataError(
                    f"Missing required field '{field}' "
                    f"in item #{index} of state '{target}'"
                )
