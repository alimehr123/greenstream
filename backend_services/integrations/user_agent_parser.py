# backend_services/integrations/user_agent_parser.py

from fastapi import Request
from typing import Dict


def get_client_ip(request: Request) -> str:
    """
    Extracts client IP address from request headers or connection info.

    IO-layer function.
    No inference or decision-making.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()

    if request.client:
        return request.client.host

    return "unknown"


def parse_user_agent(user_agent: str) -> Dict[str, str]:
    """
    Parses raw User-Agent string into normalized, factual descriptors.

    WARNING:
    --------
    This function MUST remain fact-only.
    No UI, policy, or capability decisions are allowed here.
    """

    ua = (user_agent or "").lower()

    # --------------------
    # Device detection
    # --------------------
    device = "web"
    if "mobile" in ua or "android" in ua or "iphone" in ua:
        device = "mobile"
    elif "windows" in ua or "macintosh" in ua or "linux" in ua:
        device = "desktop"

    # --------------------
    # Operating system
    # --------------------
    op_sys = "unknown"
    if "windows" in ua:
        op_sys = "windows"
    elif "android" in ua:
        op_sys = "android"
    elif "iphone" in ua or "ios" in ua:
        op_sys = "ios"
    elif "macintosh" in ua:
        op_sys = "macos"
    elif "linux" in ua:
        op_sys = "linux"

    # --------------------
    # Browser detection
    # --------------------
    browser = "unknown"
    if "edg" in ua:
        browser = "edge"
    elif "opr" in ua or "opera" in ua:
        browser = "opera"
    elif "chrome" in ua:
        browser = "chrome"
    elif "firefox" in ua:
        browser = "firefox"
    elif "safari" in ua and "chrome" not in ua:
        browser = "safari"

    return {
        "device": device,
        "op_sys": op_sys,
        "browser": browser,
    }
