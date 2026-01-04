# backend_services/capabilities/registry.py

from typing import Dict, Callable, Any
import inspect

from backend_services.errors import CapabilityRegistryError


class CapabilityRegistry:
    """
    Capability Registry (LOCKED)

    Responsibilities:
    -----------------
    - Register capabilities by intent name
    - Provide executable capability for dispatcher
    - Enforce minimal execution contract

    This registry:
    - DOES NOT execute capabilities
    - DOES NOT know about state, layout, or UI
    """

    def __init__(self) -> None:
        self._capabilities: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, *, intent: str, capability: Any) -> None:
        """
        Register a capability for an intent.

        Parameters:
        ----------
        intent: str
            Intent name (e.g. "search_videos", "play_video")

        capability:
            Either:
              - an object with an `execute()` method
              - a callable (async or sync)
        """

        if not intent or not isinstance(intent, str):
            raise CapabilityRegistryError("Intent name must be a non-empty string")

        if intent in self._capabilities:
            raise CapabilityRegistryError(
                f"Capability already registered for intent '{intent}'"
            )

        self._validate_capability(capability)

        self._capabilities[intent] = capability

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def get(self, intent: str) -> Callable:
        """
        Resolve an executable capability by intent.

        Returns:
        --------
        A callable executable compatible with ExecutableDispatcher.
        """

        capability = self._capabilities.get(intent)
        if not capability:
            return None

        # Object-style capability → return its execute()
        if hasattr(capability, "execute"):
            return capability

        # Function-style capability
        return capability

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_capability(self, capability: Any) -> None:
        """
        Enforce minimal executable contract.
        """

        # Object-based capability
        if hasattr(capability, "execute"):
            execute_fn = getattr(capability, "execute")
            if not callable(execute_fn):
                raise CapabilityRegistryError(
                    "Capability.execute must be callable"
                )
            self._validate_callable(execute_fn)
            return

        # Function-based capability
        if callable(capability):
            self._validate_callable(capability)
            return

        raise CapabilityRegistryError(
            "Capability must be callable or expose an execute() method"
        )

    def _validate_callable(self, fn: Callable) -> None:
        """
        Validate callable signature at a high level.

        We do NOT enforce argument names strictly,
        but we ensure callability and async compatibility.
        """
        if not callable(fn):
            raise CapabilityRegistryError("Capability is not callable")

        # Optional sanity check: async or sync allowed
        if not inspect.iscoroutinefunction(fn):
            # sync function is allowed, but warn via exception text if misused later
            pass

    # ------------------------------------------------------------------
    # Debug / Introspection
    # ------------------------------------------------------------------

    def list_intents(self):
        """
        Return all registered intents (for diagnostics / tests).
        """
        return list(self._capabilities.keys())
