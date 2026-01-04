# backend_services/intents/play_video_intent.py

from typing import Optional


class PlayVideoIntent:
    """
    Intent: Play Video

    - Represents a user's or system's desire to play a video
    - Contains NO logic
    - Contains NO UI or provider-specific behavior
    - Acts purely as a semantic data carrier
    """

    def __init__(
        self,
        video_id: str,
        provider: Optional[str] = None,
        autoplay: bool = True,
    ):
        if not video_id:
            raise ValueError("video_id is required for PlayVideoIntent")

        self.video_id = video_id
        self.provider = provider or "youtube"
        self.autoplay = autoplay

    def to_dict(self) -> dict:
        """
        Optional helper for logging / debugging.
        NOT used by the Capability or Aggregator directly.
        """
        return {
            "video_id": self.video_id,
            "provider": self.provider,
            "autoplay": self.autoplay,
        }
