# server/services/IO_context_services/youtube_service.py

import os
import re
import requests
from datetime import timedelta
from typing import List, Dict, Any

# ------------------------------------------------------------------
# Configuration (IO / Infra Layer)
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


def _parse_duration(iso_duration: str) -> str:
    """
    Convert ISO 8601 duration to display-safe string.

    Examples:
        PT1H2M10S -> 01:02:10
        PT5M4S    -> 05:04

    This function performs parsing only.
    It contains NO UI or business logic.
    """

    if not iso_duration:
        return "00:00"

    match = _DURATION_PATTERN.match(iso_duration)
    if not match:
        return "00:00"

    hours, minutes, seconds = match.groups()

    td = timedelta(
        hours=int(hours or 0),
        minutes=int(minutes or 0),
        seconds=int(seconds or 0),
    )

    total_seconds = int(td.total_seconds())
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60

    if h > 0:
        return f"{h:02}:{m:02}:{s:02}"

    return f"{m:02}:{s:02}"


# ------------------------------------------------------------------
# Public IO Functions (YouTube Data API)
# ------------------------------------------------------------------

def search_videos(
    query: str,
    max_results: int = 10,
) -> List[Dict[str, Any]]:
    """
    Search YouTube videos.

    IO-only responsibility:
    - Call external API
    - Return raw, provider-specific data
    - No decisions
    - No semantic state
    """

    search_url = f"{BASE_URL}/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "key": YOUTUBE_API_KEY,
    }

    response = requests.get(search_url, params=params, timeout=10)
    response.raise_for_status()

    items = response.json().get("items", [])
    video_ids = [
        item["id"]["videoId"]
        for item in items
        if item.get("id", {}).get("videoId")
    ]

    if not video_ids:
        return []

    return get_videos_details(video_ids)


def get_videos_details(
    video_ids: List[str],
) -> List[Dict[str, Any]]:
    """
    Fetch detailed metadata for a list of YouTube video IDs.

    Returns provider-specific, raw data
    suitable ONLY for consumption by Capabilities.
    """

    videos_url = f"{BASE_URL}/videos"
    params = {
        "part": "snippet,statistics,contentDetails",
        "id": ",".join(video_ids),
        "key": YOUTUBE_API_KEY,
    }

    response = requests.get(videos_url, params=params, timeout=10)
    response.raise_for_status()

    items = response.json().get("items", [])
    videos: List[Dict[str, Any]] = []

    for item in items:
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        content_details = item.get("contentDetails", {})

        videos.append({
            "source": "youtube",
            "video_id": item.get("id"),
            "title": snippet.get("title", ""),
            "channel_title": snippet.get("channelTitle", ""),
            "thumbnail": (
                snippet.get("thumbnails", {})
                .get("medium", {})
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
