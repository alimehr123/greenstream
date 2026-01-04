# backend_services/capabilities/search_videos.py

from typing import Dict, Any, List


# ✅ Intent definition (explicit & immutable)
class SearchVideosIntent:
    def __init__(self, query: str):
        self.intent = "search_videos"
        self.query = query


# ✅ Capability: sole decision owner
async def execute(
    intent: SearchVideosIntent,
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Capability: search_videos (LOCKED)

    Responsibilities:
    - Execute video search IO
    - Resolve all business decisions
    - Emit semantic, UI-ready state patches ONLY

    MUST NOT:
    - Emit UI modes, layouts, renderer hints
    - Mix multiple semantic meanings into one state
    """

    query = intent.query

    # --------------------
    # IO / External service
    # --------------------
    from server.services.youtube_service_async import search_videos_async

    raw_videos: List[Dict[str, Any]] = await search_videos_async(query)

    # --------------------
    # Semantic decision resolution
    # --------------------
    search_results: List[Dict[str, Any]] = []

    for video in raw_videos or []:
        video_id = video.get("video_id")

        if not video_id:
            continue  # defensive: malformed IO result

        search_results.append({
            "provider": "youtube",
            "video_id": video_id,
            "title": video.get("title", ""),
            "thumbnail_url": video.get("thumbnail"),
            "watch_url": f"https://www.youtube.com/watch?v={video_id}",
        })

    # --------------------
    # State patches (Registry + Aggregator compatible ✅)
    # --------------------
    return {
        "state_patches": [
            {
                "target": "search_results",
                "owner": "page",
                "page": "search",
                "lifecycle": {
                    "create": "page_enter",
                    "destroy": "page_exit",
                },
                # ✅ MUST be array (per schema)
                "data": search_results,
            }
        ]
    }
