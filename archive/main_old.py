"""
main.py

FastAPI entry point for GreenStream backend.

Responsibilities:
- API orchestration only
- Profile/context resolution
- Route definitions
- Delegation to domain services and UI schema builders

Constraints:
- No business logic
- No UI construction logic
"""

import os
import sys
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse


# =========================
# Path Resolution (Root Import)
# =========================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# shared_config lives in project root (outside /server)
from shared_config import get_base_url


# =========================
# Local Imports (After sys.path fix)
# =========================

from services.youtube_service import search_videos, get_video_details
from ui_schema.ui_schema import (
    build_home_schema,
    build_search_results_schema,
    build_player_schema,
)


# =========================
# App Initialization
# =========================

app = FastAPI(title="GreenStream Backend")


# =========================
# Helpers
# =========================

def resolve_profile() -> str:
    """
    Resolve user context profile.

    For MVP:
    - Always returns 'generic'
    - Can later be extended to auth/session-based profiles
    """
    return "generic"


def ui_response(schema: Dict[str, Any]) -> JSONResponse:
    """
    Standard UI schema JSON response wrapper.
    """
    return JSONResponse(content=schema)


# =========================
# Bootstrap Endpoint
# =========================

@app.get("/")
def bootstrap_ui():
    """
    Entry point for all clients.

    Returns:
    - UI schema for home screen
    - Always includes profile context
    """
    profile = resolve_profile()
    schema = build_home_schema(profile=profile)
    return ui_response(schema)


# =========================
# Search API
# =========================

@app.post("/api/search")
def search_api(payload: Dict[str, Any]):
    """
    Perform video search and return UI update schema.
    """
    query = payload.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="Missing search query")

    profile = resolve_profile()

    results = search_videos(query)
    schema = build_search_results_schema(
        results=[r.__dict__ for r in results],
        profile=profile,
    )
    return ui_response(schema)


# =========================
# Select / Play API
# =========================

@app.post("/api/select")
def select_video(payload: Dict[str, Any]):
    """
    Handle user selecting a video.
    """
    video_id = payload.get("video_id")
    if not video_id:
        raise HTTPException(status_code=400, detail="Missing video_id")

    profile = resolve_profile()

    details = get_video_details(video_id)
    if details is None:
        raise HTTPException(status_code=404, detail="Video not available")

    schema = build_player_schema(
        video_details=details.__dict__,
        profile=profile,
    )
    return ui_response(schema)


# =========================
# SPA Fallback (Web UI)
# =========================

UI_WEB_DIR = os.path.join(BASE_DIR, "ui_web")
INDEX_HTML = os.path.join(UI_WEB_DIR, "index.html")


@app.get("/{full_path:path}")
def spa_fallback(full_path: str):
    """
    Serve SPA index.html for all unmatched routes.
    """
    if os.path.exists(INDEX_HTML):
        return FileResponse(INDEX_HTML)

    raise HTTPException(status_code=404, detail="UI not found")
