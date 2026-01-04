# backend_services/integrations/request_context_builder.py

from fastapi import Request
from datetime import datetime
from typing import Dict

from .user_agent_parser import parse_user_agent, get_client_ip


def build_request_context(request: Request) -> Dict[str, object]:
    """
    IO / Context Fact Collector (LOCKED)

    Responsibilities:
    -----------------
    - Collect raw request & environment facts
    - Normalize headers and metadata
    - Provide a stable, decision-free context object

    MUST NOT:
    ---------
    - Make UI decisions
    - Resolve layout or policy
    - Build or mutate State
    - Infer meaning from facts
    """

    # --------------------
    # User-Agent parsing
    # --------------------
    ua = request.headers.get("user-agent", "")
    ua_info = parse_user_agent(ua)

    # --------------------
    # Network / headers
    # --------------------
    ip = get_client_ip(request)

    raw_lang = request.headers.get("accept-language", "en-US")
    language = raw_lang.split(",")[0].strip() or "en-US"

    app_channel = request.headers.get("x-app-channel", "web")

    # --------------------
    # Context assembly
    # --------------------
    context = {
        # Device & agent facts
        "device": ua_info.get("device", "web"),
        "op_sys": ua_info.get("op_sys", "unknown"),
        "browser": ua_info.get("browser", "unknown"),

        # Network
        "ip_address": ip,
        "connectivity": "unknown",
        "language": language,
        "country": None,
        "timezone": None,

        # User (fact-only placeholders)
        "user_type": "guest",
        "user_id": None,
        "permissions": [],

        # Application environment
        "app_version": "1.0.0",
        "app_channel": app_channel,
        "screen_size": None,
        "theme": None,

        # Meta
        "request_time": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "user_agent": ua,
        "extra": {},
    }

    return context
