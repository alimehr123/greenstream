# backend_services/layout_services/layout_compiler.py

from typing import Dict, Any, List


# ----------------------------------------------------------------------
# Custom Error Type
# ----------------------------------------------------------------------
class LayoutCompileError(Exception):
    """
    Raised when a layout definition violates the LOCKED Layout Contract.

    IMPORTANT:
    Every error message raised from this compiler MUST be:
    - Explicit
    - Self-explanatory
    - Pointing to the exact location and cause of the problem
    """
    pass


# ----------------------------------------------------------------------
# Public Compiler API
# ----------------------------------------------------------------------
def compile_layout(layout_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compile a Raw Layout Schema into a renderer-ready, self-contained layout.

    This function acts as a STRICT ARCHITECTURAL BOUNDARY.

    Responsibilities (as defined in layout_compiler.docx):
    - Enforce top-level schema invariants
    - Perform structural validation
    - Resolve all references (pages -> components -> actions)
    - Produce a deterministic, runtime-safe output

    Forbidden:
    - Decision making of any kind
    - Meta / SEO / Context handling
    - State mutation or derivation
    """

    # ------------------------------------------------------------------
    # 0. Defensive type check
    # ------------------------------------------------------------------
    if not isinstance(layout_schema, dict):
        raise LayoutCompileError(
            "[layout_compiler] Invalid input type.\n"
            "Expected layout schema to be a JSON object (dict).\n"
            "Please check the root of your layout file."
        )

    # ------------------------------------------------------------------
    # 1. Top-level schema enforcement (LOCKED)
    # ------------------------------------------------------------------
    # According to the Layout Contract, the root object MUST contain
    # exactly these keys — no more, no less.
    required_top_level_keys = {
        "identity",
        "policy",
        "navigation",
        "state",
        "pages",
        "components",
        "actions",
        "interactions",
    }

    actual_keys = set(layout_schema.keys())

    # ---- Missing keys (explicit listing) ----
    missing_keys = required_top_level_keys - actual_keys
    if missing_keys:
        raise LayoutCompileError(
            "[layout_compiler] Top-level schema violation detected.\n"
            f"The following REQUIRED top-level keys are MISSING: {sorted(missing_keys)}\n\n"
            "Every layout file MUST declare all locked top-level sections.\n"
            "Please add the missing sections to the root of your layout JSON.\n\n"
            "Expected top-level keys:\n"
            f"{sorted(required_top_level_keys)}"
        )

    # ---- Extra / forbidden keys (explicit listing) ----
    extra_keys = actual_keys - required_top_level_keys
    if extra_keys:
        raise LayoutCompileError(
            "[layout_compiler] Top-level schema violation detected.\n"
            f"The following FORBIDDEN top-level keys were found: {sorted(extra_keys)}\n\n"
            "The Layout Contract is LOCKED.\n"
            "No additional root-level keys are allowed.\n"
            "If this data represents metadata, context, or policy decisions,\n"
            "it MUST be moved outside of the layout system."
        )

    # ------------------------------------------------------------------
    # 2. Extract top-level sections (now guaranteed to exist)
    # ------------------------------------------------------------------
    identity = layout_schema["identity"]
    navigation = layout_schema["navigation"]
    state = layout_schema["state"]

    pages = layout_schema["pages"]
    components_def = layout_schema["components"]
    actions_def = layout_schema["actions"]
    
    # ------------------------------------------------------------------
    # 3. Basic structural checks (explicit & localized)
    # ------------------------------------------------------------------

    # ---- Pages ----
    if not isinstance(pages, list):
        raise LayoutCompileError(
            "[layout_compiler] Invalid type for 'pages'.\n"
            f"Expected 'pages' to be an array, got: {type(pages).__name__}\n\n"
            "According to the Layout Contract, 'pages' MUST be a non-empty array."
        )

    if not pages:
        raise LayoutCompileError(
            "[layout_compiler] Invalid layout: no pages defined.\n"
            "The 'pages' array is empty.\n\n"
            "At least one page must be declared for a layout to be valid."
        )

    # ---- Components ----
    if not isinstance(components_def, dict):
        raise LayoutCompileError(
            "[layout_compiler] Invalid type for 'components'.\n"
            f"Expected an object (dictionary), got: {type(components_def).__name__}\n\n"
            "Components must be declared as a dictionary keyed by component ID."
        )

    # ---- Actions ----
    if not isinstance(actions_def, dict):
        raise LayoutCompileError(
            "[layout_compiler] Invalid type for 'actions'.\n"
            f"Expected an object (dictionary), got: {type(actions_def).__name__}\n\n"
            "Actions must be declared as a dictionary keyed by action ID."
        )

    # ------------------------------------------------------------------
    # 4. Compile pages (resolve component references)
    # ------------------------------------------------------------------
    compiled_pages: List[Dict[str, Any]] = []

    for page_index, page in enumerate(pages):
        page_id = page.get("id")

        # ---- Page ID check ----
        if not page_id:
            raise LayoutCompileError(
                "[layout_compiler] Page validation error.\n"
                f"Page at index {page_index} is missing required field 'id'.\n\n"
                "Every page object MUST declare a unique 'id'."
            )

        component_ids = page.get("components")

        # ---- Components list check ----
        if not isinstance(component_ids, list):
            raise LayoutCompileError(
                "[layout_compiler] Page validation error.\n"
                f"Page '{page_id}' has invalid 'components' field.\n"
                f"Expected an array of component IDs, got: {type(component_ids).__name__}"
            )

        resolved_components: List[Dict[str, Any]] = []

        # ------------------------------------------------------------------
        # Resolve each component reference declared by this page
        # ------------------------------------------------------------------
        for component_id in component_ids:
            component_def = components_def.get(component_id)

            if component_def is None:
                raise LayoutCompileError(
                    "[layout_compiler] Component reference error.\n"
                    f"Page '{page_id}' references component '{component_id}',\n"
                    "but no such component is declared in the 'components' section.\n\n"
                    "Please ensure that every referenced component ID exists."
                )

            resolved_components.append(
                _compile_component(
                    component_id=component_id,
                    component_def=component_def,
                    actions_def=actions_def,
                    page_id=page_id,
                )
            )

        # ---- Compiled page projection ----
        compiled_pages.append(
            {
                "id": page_id,
                "title": page.get("title"),
                "components": resolved_components,
            }
        )

    # ------------------------------------------------------------------
    # 5. Final projection (policy / interactions intentionally excluded)
    # ------------------------------------------------------------------
    # The renderer only receives what it is allowed to know.
    return {
        "identity": identity,
        "navigation": navigation,
        "state": state,
        "pages": compiled_pages,
    }


# ----------------------------------------------------------------------
# Internal helpers
# ----------------------------------------------------------------------
def _compile_component(
    component_id: str,
    component_def: Dict[str, Any],
    actions_def: Dict[str, Any],
    page_id: str,
) -> Dict[str, Any]:
    """
    Resolve a component definition into a renderer-safe object.

    This function:
    - Validates component shape
    - Resolves event -> action references
    - Does NOT interpret meaning
    """

    component_type = component_def.get("type")
    if not component_type:
        raise LayoutCompileError(
            "[layout_compiler] Component validation error.\n"
            f"Component '{component_id}' (used in page '{page_id}') "
            "is missing required field 'type'.\n\n"
            "Every component MUST declare its type explicitly."
        )

    compiled_component: Dict[str, Any] = {
        "id": component_id,
        "type": component_type,
    }

    # ---- Static state bindings (read-only) ----
    if "bind" in component_def:
        compiled_component["bind"] = component_def["bind"]

    # ---- Resolve events -> actions ----
    events = component_def.get("events", {})

    if not isinstance(events, dict):
        raise LayoutCompileError(
            "[layout_compiler] Component validation error.\n"
            f"Component '{component_id}' has invalid 'events' field.\n"
            f"Expected an object, got: {type(events).__name__}"
        )

    resolved_events: Dict[str, Dict[str, Any]] = {}

    for event_name, action_id in events.items():
        action_def = actions_def.get(action_id)

        if action_def is None:
            raise LayoutCompileError(
                "[layout_compiler] Action reference error.\n"
                f"Component '{component_id}' declares event '{event_name}' "
                f"linked to action '{action_id}',\n"
                "but no such action exists in the 'actions' section.\n\n"
                "Please declare the action or fix the reference."
            )

        resolved_events[event_name] = {
            "id": action_id,
            "intent": action_def.get("intent"),
            "target": action_def.get("target"),
            "params": action_def.get("params", {}),
        }

    if resolved_events:
        compiled_component["events"] = resolved_events

    return compiled_component

# ----------------------------------------------------------------------
# Public alias for UI Orchestrator (LOCKED API)
# ----------------------------------------------------------------------

def compile_layout_to_render_tree(layout_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    UI-facing alias for layout compilation.

    This function exists to preserve a clear semantic contract:
    - UI Orchestrator compiles layout into a renderer-ready render tree
    - Actual compilation logic lives in `compile_layout`

    IMPORTANT:
    This is a pure alias. No additional logic is allowed here.
    """
    return compile_layout(layout_schema)
