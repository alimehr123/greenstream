# server/api/video.py

from fastapi import APIRouter, HTTPException, Request
from typing import Dict, Any

from backend_services.capabilities.play_video import (
    execute as play_video_execute,
    PlayVideoIntent,
)

from backend_services.integrations.request_context_builder import (
    build_request_context,
)

router = APIRouter()


@router.post("/video")
async def video_endpoint(
    payload: Dict[str, Any],
    request: Request,
) -> Dict[str, Any]:
    """
    HTTP Adapter (LOCKED)

    Responsibilities:
    -----------------
    - Receive HTTP request
    - Validate transport payload
    - Build Intent
    - Build Context (facts only)
    - Delegate to Capability
    - Return Capability result verbatim

    MUST NOT:
    ---------
    - Build pages or components
    - Embed iframe / UI logic
    - Know about providers (YouTube, etc.)
    """

    video_id = payload.get("video_id")

    if not video_id:
        raise HTTPException(
            status_code=400,
            detail="video_id is required",
        )

    # --------------------
    # Build Intent
    # --------------------
    intent = PlayVideoIntent(
        video_id=video_id
    )

    # --------------------
    # Build Context
    # --------------------
    context = build_request_context(request)

    # --------------------
    # Delegate to Capability
    # --------------------
    result = await play_video_execute(
        intent=intent,
        context=context,
    )

    return result
