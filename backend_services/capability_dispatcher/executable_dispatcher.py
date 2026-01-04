# backend_services/capability_dispatcher/executable_dispatcher.py

from typing import Dict, Any

from backend_services.state_aggregation.ui_state_aggregator import aggregate_ui_state
from backend_services.capability_dispatcher.errors import (
    CapabilityExecutionError,
)



class ExecutableDispatcher:
    """
    Executable Dispatcher (LOCKED)

    Responsibilities:
    -----------------
    - Resolve and execute a capability
    - Enforce execution contract
    - Forward state patches to the UI State Aggregator
    - NO decision-making
    - NO domain knowledge
    """

    def __init__(self, capability_registry):
        """
        capability_registry:
            An object exposing:
                - get(intent_name) -> callable
        """
        self._registry = capability_registry

    async def dispatch(
        self,
        *,
        action: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Dispatch an intent to its executable capability.
        """

        intent_name = action.get("intent")
        if not intent_name:
            raise CapabilityExecutionError("Missing intent in action")

        capability = self._registry.get(intent_name)
        if not capability:
            raise CapabilityExecutionError(
                f"No capability registered for intent '{intent_name}'"
            )

        # ✅ Capability execution phase
        try:
            result = await capability.execute(
                intent=intent_name,
                context=context,
                action=action,
            )
        except Exception as exc:
            # HARD crash of capability = backend bug
            raise CapabilityExecutionError(
                f"Capability '{intent_name}' execution failed: {exc}"
            ) from exc

        if not isinstance(result, dict):
            raise CapabilityExecutionError(
                f"Capability '{intent_name}' must return a dict"
            )

        state_patches = result.get("state_patches")
        if not isinstance(state_patches, list):
            raise CapabilityExecutionError(
                f"Capability '{intent_name}' must return 'state_patches' as a list"
            )

        # ✅ Aggregation (schema validation happens inside)
        return aggregate_ui_state(
            context=context,
            state_patches=state_patches,
        )
