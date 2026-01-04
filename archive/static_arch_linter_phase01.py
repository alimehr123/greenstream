# tools/static_arch_linter.py
# Phase 1 – Full Dynamic Architecture Import Linter

import ast
from pathlib import Path
from typing import Dict, List, Optional


# -----------------------------
# CONFIGURATION
# -----------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend_services"

REPORT_DIR = PROJECT_ROOT / "architecture_reports"
REPORT_DIR.mkdir(exist_ok=True)

REPORT_FILE = REPORT_DIR / "import_violations_report.txt"
SUMMARY_FILE = REPORT_DIR / "import_violations_summary.txt"


# -----------------------------
# LAYER DISCOVERY
# -----------------------------

def discover_layers(root: Path) -> List[str]:
    """
    Every first-level directory under backend_services
    is treated as an architecture layer.
    """
    return sorted([
        p.name for p in root.iterdir()
        if p.is_dir() and not p.name.startswith("__")
    ])


LAYER_ORDER = discover_layers(BACKEND_ROOT)
LAYER_INDEX = {layer: idx for idx, layer in enumerate(LAYER_ORDER)}


# -----------------------------
# FILE & IMPORT DISCOVERY
# -----------------------------

def discover_python_files(root: Path) -> List[Path]:
    return [p for p in root.rglob("*.py") if p.is_file()]


def detect_layer(file_path: Path) -> Optional[str]:
    for part in file_path.parts:
        if part in LAYER_INDEX:
            return part
    return None


def extract_imports(file_path: Path) -> List[str]:
    imports = []
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except Exception:
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.append(n.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    return imports


def infer_import_layer(import_stmt: str) -> Optional[str]:
    for part in import_stmt.split("."):
        if part in LAYER_INDEX:
            return part
    return None


# -----------------------------
# LINT ENGINE
# -----------------------------

def lint() -> Dict:
    violations = []
    checked_files = 0

    for file_path in discover_python_files(BACKEND_ROOT):
        checked_files += 1

        source_layer = detect_layer(file_path)
        imports = extract_imports(file_path)

        for imp in imports:
            target_layer = infer_import_layer(imp)

            if not source_layer or not target_layer:
                continue

            if LAYER_INDEX[target_layer] > LAYER_INDEX[source_layer]:
                violations.append({
                    "file": str(file_path),
                    "from_layer": source_layer,
                    "import": imp,
                    "to_layer": target_layer,
                })

    return {
        "checked_files": checked_files,
        "layers": LAYER_ORDER,
        "violations": violations,
    }


# -----------------------------
# REPORTING
# -----------------------------

def write_reports(result: Dict):
    with REPORT_FILE.open("w", encoding="utf-8") as f:
        f.write("=== Architecture Import Violations ===\n\n")
        f.write(f"Detected layers:\n  {', '.join(result['layers'])}\n\n")

        if not result["violations"]:
            f.write("✅ No violations found.\n")
        else:
            for v in result["violations"]:
                f.write(
                    f"- {v['file']}\n"
                    f"  from: {v['from_layer']}\n"
                    f"  imports: {v['import']}\n"
                    f"  to: {v['to_layer']}\n\n"
                )

    with SUMMARY_FILE.open("w", encoding="utf-8") as f:
        f.write("=== Summary ===\n\n")
        f.write(f"Checked files: {result['checked_files']}\n")
        f.write(f"Layers detected: {len(result['layers'])}\n")
        f.write(f"Violations: {len(result['violations'])}\n")


# -----------------------------
# ENTRY
# -----------------------------

if __name__ == "__main__":
    result = lint()
    write_reports(result)

    print("✅ Full Dynamic Architecture Linter completed")
    print(f"Layers: {LAYER_ORDER}")
    print(f"Report: {REPORT_FILE}")
