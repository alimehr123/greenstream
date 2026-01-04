# backend_services/state_aggregation/errors.py

class StateSchemaError(Exception):
    """Base class for state schema violations."""


class UnknownStateTargetError(StateSchemaError):
    pass


class InvalidStateOwnerError(StateSchemaError):
    pass


class InvalidStateLifecycleError(StateSchemaError):
    pass


class InvalidStateDataError(StateSchemaError):
    pass
