# backend_services/layout_policy/ui_layout_resolver.py

from typing import Dict, Any, List


# ------------------------------------------------------------------------------
# Rule-Based UI Layout Resolver
# Responsibilities:
# - Decide WHICH layout should be used
# - Return layout_name as string
# - NO loading, NO IO, NO schema access
# ------------------------------------------------------------------------------

LAYOUT_RULES: List[Dict[str, Any]] = [
    {
        # Highest priority
        "when": {
            "app_channel": "desktop_offline",
            "op_sys": "windows",
            "user_type": "guest",
        },
        "layout": "desktop",
    },
    {
        "when": {
            "device": "mobile",
            "user_type": "guest",
        },
        "layout": "mobile",
    },
    {
        "when": {
            "device": "web",
            "user_type": "guest",
        },
        "layout": "web_guest",
    },
]


DEFAULT_LAYOUT = "search_and_play"


def match_rule(context: Dict[str, Any], rule: Dict[str, Any]) -> bool:
    """
    Return True if ALL rule['when'] conditions match the context.
    """
    for key, expected in rule["when"].items():
        if context.get(key) != expected:
            return False
    return True


def resolve_ui_layout(context: Dict[str, Any]) -> str:
    """
    Resolve layout_name using rule-based matching.
    This function is PURE and side-effect free.
    """
    for rule in LAYOUT_RULES:
        if match_rule(context, rule):
            return rule["layout"]

    return DEFAULT_LAYOUT
