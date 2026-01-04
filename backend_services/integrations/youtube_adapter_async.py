# server/services/IO_context_services/youtube_service_async.py

import os
import re
import httpx
from typing import List, Dict, Any

# ------------------------------------------------------------------
# Configuration (IO / Infrastructure Layer)
# ------------------------------------------------------------------

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
BASE_URL = "https://www.googleapis.com/youtube/v3"


# ------------------------------------------------------------------
# Internal Helpers (Pure Parsing Only)
# ------------------------------------------------------------------

_DURATION_PATTERN = re.compile(
    r"PT"
    r"(?:(\d+)H)?"
    r"(?:(\d+)M)?"
    r"(?:(\d+)S)?"
)


def _parse_duration(iso_duration: str) -> int:
    """
    Parse ISO-8601 duration (PT#H#M#S) into total seconds.

    - Defensive
    - Never raises
    - Pure parsing only
    """

    if not iso_duration or not isinstance(iso_duration, str):
        return 0

    match = _DURATION_PATTERN.match(iso_duration)
    if not match:
        return 0

    hours, minutes, seconds = match.groups()

    return (
        int(hours or 0) * 3600
        + int(minutes or 0) * 60
        + int(seconds or 0)
    )


# ------------------------------------------------------------------
# Public Async IO Functions (YouTube Data API)
# ------------------------------------------------------------------

async def search_videos_async(
    query: str,
    max_results: int = 10,
) -> List[Dict[str, Any]]:
    """
    Async YouTube search.

    IO-only responsibility:
    - External API calls
    - Raw provider data
    - No decisions
    - No semantic state
    """

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            f"{BASE_URL}/search",
            params={
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": max_results,
                "key": YOUTUBE_API_KEY,
            },
        )
        response.raise_for_status()
        items = response.json().get("items", [])

        video_ids = [
            item.get("id", {}).get("videoId")
            for item in items
            if item.get("id", {}).get("videoId")
        ]

        if not video_ids:
            return []

        return await get_videos_details_async(video_ids)


async def get_videos_details_async(
    video_ids: List[str],
) -> List[Dict[str, Any]]:
    """
    Fetch detailed metadata for YouTube video IDs (async).

    Returns raw, provider-specific data
    suitable ONLY for Capability consumption.
    """

    if not video_ids:
        return []

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            f"{BASE_URL}/videos",
            params={
                "part": "snippet,statistics,contentDetails",
                "id": ",".join(video_ids),
                "key": YOUTUBE_API_KEY,
            },
        )
        response.raise_for_status()
        items = response.json().get("items", [])

    videos: List[Dict[str, Any]] = []

    for v in items:
        snippet = v.get("snippet", {})
        statistics = v.get("statistics", {})
        content_details = v.get("contentDetails", {})
        thumbnails = snippet.get("thumbnails", {})

        videos.append({
            "source": "youtube",
            "video_id": v.get("id"),
            "title": snippet.get("title", ""),
            "channel_title": snippet.get("channelTitle", ""),
            "thumbnail": (
                thumbnails.get("medium", {})
                .get("url")
                or thumbnails.get("default", {})
                .get("url")
            ),
            "description": snippet.get("description", ""),
            "published_at": snippet.get("publishedAt"),
            "view_count": int(statistics.get("viewCount", 0)),
            "duration": _parse_duration(
                content_details.get("duration")
            ),
        })

    return videos
