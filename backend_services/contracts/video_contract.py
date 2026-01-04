# server/contracts/video_contract.py

REQUIRED_FIELDS = {
    "source": str,
    "video_id": str,
    "title": str,
    "channel_title": str,
    "thumbnail": str,
    "description": str,   # ✅ allowed to be empty
    "published_at": str,
    "view_count": int,
    "duration": str,
}

# String fields that MUST NOT be empty
NON_EMPTY_STR_FIELDS = {
    "video_id",
    "title",
    "channel_title",
    "thumbnail",
    "published_at",
    "duration",
}


def assert_video_contract(video: dict) -> None:
    assert isinstance(video, dict), "Video must be a dict"

    for field, expected_type in REQUIRED_FIELDS.items():
        assert field in video, f"Missing field: '{field}'"

        value = video[field]
        assert isinstance(
            value, expected_type
        ), f"Field '{field}' must be {expected_type.__name__}, got {type(value).__name__}"

        if field in NON_EMPTY_STR_FIELDS:
            assert value.strip() != "", f"Field '{field}' cannot be empty"

    assert video["source"] == "youtube", (
        f"Invalid source: expected 'youtube', got '{video['source']}'"
    )
