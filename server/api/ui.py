# server/api/ui.py

"""
UI Orchestrator (LOCKED ✅)

ROLE:
-----
Single orchestration entry point for UI bootstrap.

Responsibilities:
- Gather request context (IO only)
- Resolve layout policy (decision → layout name)
- Load and compile layout (structure only)
- Dispatch backend capabilities (via Dispatcher)
- Aggregate UI State (State Patch model)
- Finalize UI response (hard boundary enforcement)

This module MUST NOT:
- Build, mutate, or interpret State
- Inspect layout semantics
- Execute capabilities directly
- Merge capability outputs manually
- Perform schema validation (handled by middleware)
"""

from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any

# -----------------------------
# IO / Context
# -----------------------------
from backend_services.integrations.request_context_builder import (
    build_request_context,
)

# -----------------------------
# Layout Policy & Tooling
# -----------------------------
from backend_services.layout_policy.ui_layout_resolver import (
    resolve_ui_layout,
)

from backend_services.layout_services.layout_loader import load_layout
from backend_services.layout_services.layout_compiler import (
    compile_layout_to_render_tree,
)

# -----------------------------
# Capability Dispatcher
# -----------------------------
from backend_services.capability_dispatcher.executable_dispatcher import (
    ExecutableDispatcher,
)

# -----------------------------
# State Aggregation
# -----------------------------
from backend_services.state_aggregation.ui_state_aggregator import (
    aggregate_ui_state,
)

# -----------------------------
# Final Boundary
# -----------------------------
from backend_services.finalization.ui_response_finalizer import (
    finalize_ui_response,
)

router = APIRouter()

# ------------------------------------------------------------------
# Dispatcher injection (mandatory bootstrap step)
# ------------------------------------------------------------------

_dispatcher: ExecutableDispatcher | None = None


def init_ui_router(*, dispatcher: ExecutableDispatcher):
    """
    Inject ExecutableDispatcher at application startup.

    This keeps the UI layer decoupled from capability wiring.
    """
    global _dispatcher
    _dispatcher = dispatcher


# ------------------------------------------------------------------
# UI Entry Point (LOCKED)
# ------------------------------------------------------------------

@router.get("/ui")
async def get_ui(request: Request) -> Dict[str, Any]:
    """
    UI bootstrap entry point.

    Contract:
    ---------
    - Returns a fully UI-ready response
    - Layout is declarative and decision-free
    - State is aggregated, semantic, and owned
    - Renderer is logic-blind
    """

    if _dispatcher is None:
        raise RuntimeError("UI Dispatcher is not initialized")

    # --------------------------------------------------
    # 1️⃣ Context Gathering (IO only)
    # --------------------------------------------------
    context = build_request_context(request)

    # --------------------------------------------------
    # 2️⃣ Layout Policy Resolution (decision → layout name)
    # --------------------------------------------------
    layout_name = resolve_ui_layout(context)

    # --------------------------------------------------
    # 3️⃣ Load Raw Layout Schema (declarative)
    # --------------------------------------------------
    layout_schema = load_layout(layout_name)

    # --------------------------------------------------
    # 4️⃣ Compile Layout (structure only — NO state)
    # --------------------------------------------------
    compiled_layout = compile_layout_to_render_tree(layout_schema)

    # --------------------------------------------------
    # 5️⃣ Execute Capabilities (via Dispatcher)
    # --------------------------------------------------
    try:
        execution_result = await _dispatcher.dispatch(
            action={
                "intent": "ui_bootstrap",
                "layout": layout_name,
            },
            context=context,
        )
    except Exception as e:
        # Capability / orchestration failures are fatal
        raise HTTPException(status_code=500, detail=str(e))

    # --------------------------------------------------
    # 6️⃣ Aggregate State (State Patch Model ✅)
    # --------------------------------------------------
    aggregated = aggregate_ui_state(
        execution_result.get("state_patches", [])
    )

    # --------------------------------------------------
    # 7️⃣ Finalize Response (HARD BOUNDARY)
    # --------------------------------------------------
    return finalize_ui_response(
        layout=compiled_layout,
        state=aggregated["state"],
        actions=aggregated.get("actions"),
    )
