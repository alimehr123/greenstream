# backend_services/capabilities/play_video.py

from typing import Dict, Any
from backend_services.intents.play_video_intent import PlayVideoIntent


def play_video_execute(
    intent: PlayVideoIntent,
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Capability: play_video (LOCKED)

    - All decisions happen here
    - Produces semantic, UI‑ready state patches
    - Aggregator & Schema Registry compliant
    """

    video_id = intent.video_id

    if not video_id:
        return {
            "state_patches": [
                {
                    "key": "video_player",
                    "owner": "page",
                    "page": "player",
                    "patch": {
                        "status": "error",
                        "error_message": "Missing video_id"
                    },
                }
            ]
        }

    provider = "youtube"
    watch_url = f"https://www.youtube.com/watch?v={video_id}"

    return {
        "state_patches": [
            {
                "key": "video_player",
                "owner": "page",
                "page": "player",
                "patch": {
                    "status": "ready",
                    "provider": provider,
                    "video_id": video_id,
                    "watch_url": watch_url,
                    "autoplay": True,
                },
            }
        ]
    }
# ✅ REQUIRED ENTRY POINT FOR DISPATCHER
def execute(intent: PlayVideoIntent, context: Dict[str, Any]) -> Dict[str, Any]:
    return play_video_execute(intent, context)