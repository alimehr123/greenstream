# backend_services/capability_dispatcher/errors.py

class CapabilityExecutionError(Exception):
    """
    Raised when a capability fails during execution.

    This error represents a boundary failure between:
    - UI Action Intent
    - Capability execution
    - State patch generation

    Capabilities are allowed to fail fast using this error.
    """
    pass
