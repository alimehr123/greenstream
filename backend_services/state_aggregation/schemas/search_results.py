# backend_services/state_aggregation/schemas/search_results.py

STATE_SCHEMA = {
    "target": "search_results",

    # Page-owned semantic state
    "owner": "page",
    "page": "search",

    # UI semantic type (Layout Contract)
    "type": "array",

    "lifecycle": {
        "create": "page_enter",
        "destroy": "page_exit",
    },

    # Each Capability emitting this state MUST include these
    # fields at the top-level of data items
    "required_fields": [
        "provider",
        "video_id",
        "title",
        "thumbnail_url",
        "watch_url",
    ],
}
