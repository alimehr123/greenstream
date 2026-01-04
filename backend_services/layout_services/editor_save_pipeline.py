# backend_services/layout_services/editor_save_pipeline.py

from typing import Dict, Any

from server.services.layout_services.layout_compiler import (
     compile_layout,
     LayoutCompileError,
 )

class EditorSaveBlocked(Exception):
    pass


def run_save_pipeline(layout_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save pipeline for Layout Editor.

    Steps:
    1. Pure JSON serialization (Editor responsibility)
    2. Layout compilation (Contract validation + resolution)
    3. Block save if compilation fails
    """

    try:
        compiled_layout = compile_layout(layout_dict)
    except LayoutCompileError as e:
        raise EditorSaveBlocked(str(e)) from e

    return compiled_layout
