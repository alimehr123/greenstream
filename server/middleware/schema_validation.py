# server/middleware/schema_validation.py

"""
UI Schema Validation Middleware (LOCKED ✅)

Responsibilities:
-----------------
- Fast-fail validation of UI request contract
- Fast-fail validation of UI response wrapper
- Enforce strict Backend-Driven UI contract boundaries

This middleware performs NO business logic.
"""

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jsonschema import Draft202012Validator, ValidationError
import json
from typing import Callable

# --------------------------------------------------
# Schema Loading (LOCKED contracts)
# --------------------------------------------------

from server.schemas.loader import load_json_schema


UI_REQUEST_SCHEMA = load_json_schema("ui_request.schema.json")
UI_RESPONSE_SCHEMA = load_json_schema("ui_response.schema.json")

_request_validator = Draft202012Validator(UI_REQUEST_SCHEMA)
_response_validator = Draft202012Validator(UI_RESPONSE_SCHEMA)


# --------------------------------------------------
# Middleware
# --------------------------------------------------

class UISchemaValidationMiddleware(BaseHTTPMiddleware):
    """
    Fast-fail UI contract validation.

    Apply ONLY to UI endpoints.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:

        # ------------------------------------------
        # ✅ Validate Incoming UI Request
        # ------------------------------------------
        if request.url.path == "/api/ui":

            if request.method not in ("GET", "POST"):
                return JSONResponse(
                    status_code=405,
                    content={"error": "Method not allowed"},
                )

            if request.method == "POST":
                try:
                    body_bytes = await request.body()
                    body = json.loads(body_bytes or "{}")
                except Exception:
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid JSON body"},
                    )

                error = self._validate(_request_validator, body)
                if error:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": "UI Request Schema Validation Failed",
                            "details": error,
                        },
                    )

        # ------------------------------------------
        # ✅ Execute Request
        # ------------------------------------------
        response = await call_next(request)

        # ------------------------------------------
        # ✅ Validate Outgoing UI Response
        # ------------------------------------------
        if request.url.path == "/api/ui":
            try:
                # response.body is bytes
                response_body = response.body.decode("utf-8")
                payload = json.loads(response_body)
            except Exception:
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "UI Response is not valid JSON"
                    },
                )

            error = self._validate(_response_validator, payload)
            if error:
                return JSONResponse(
                    status_code=500,
                    content={
                        "error": "UI Response Schema Validation Failed",
                        "details": error,
                    },
                )

        return response

    # --------------------------------------------------
    # Internal helper
    # --------------------------------------------------

    @staticmethod
    def _validate(validator: Draft202012Validator, payload: dict):
        """
        Returns first schema error (if any), formatted.
        """
        try:
            validator.validate(payload)
            return None
        except ValidationError as e:
            return {
                "message": e.message,
                "path": list(e.absolute_path),
                "schema_path": list(e.absolute_schema_path),
            }
