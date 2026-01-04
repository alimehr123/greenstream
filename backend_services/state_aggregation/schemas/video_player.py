# backend_services/state_aggregation/schemas/video_player.py

STATE_SCHEMA = {
    "target": "video_player",

    # Must match Layout Contract
    "owner": "page",
    "page": "player",

    # This is NOT Python type, this is UI semantic type
    "type": "object",

    "lifecycle": {
        "create": "page_enter",
        "destroy": "page_exit",
    },

    # Capability MUST provide these keys inside data
    "required_fields": [
        "provider",
        "video_id",
        "watch_url",
        "autoplay",
    ],
}
