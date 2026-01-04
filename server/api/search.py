# server/api/search.py

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any

from backend_services.capabilities.search_videos import (
    execute as search_videos_execute,
    SearchVideosIntent,
)

from backend_services.integrations.request_context_builder import (
    build_request_context,
)

router = APIRouter()


# ✅ HTTP payload schema (transport-only)
class SearchRequest(BaseModel):
    query: str


@router.post("/search")
async def search_videos_endpoint(
    payload: SearchRequest,
    request: Request,
) -> Dict[str, Any]:
    """
    HTTP Adapter (LOCKED)

    Responsibilities:
    -----------------
    - Validate transport-level payload
    - Build explicit Intent
    - Build request Context (facts only)
    - Delegate execution to Capability
    - Return Capability result verbatim

    MUST NOT:
    ---------
    - Build State
    - Inspect layout or UI semantics
    - Modify Capability outputs
    """

    # --------------------
    # Transport validation
    # --------------------
    if not payload.query.strip():
        raise HTTPException(
            status_code=400,
            detail="Search query must not be empty",
        )

    # --------------------
    # Build Intent
    # --------------------
    intent = SearchVideosIntent(
        query=payload.query.strip()
    )

    # --------------------
    # Build Context (IO facts only)
    # --------------------
    context = build_request_context(request)

    # --------------------
    # Delegate to Capability
    # --------------------
    result = await search_videos_execute(
        intent=intent,
        context=context,
    )

    # --------------------
    # Return backend decision verbatim
    # --------------------
    return result
