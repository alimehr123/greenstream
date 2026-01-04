# tools/static_arch_linter.py
# Phase 2 – Role-Aware Semantic Architecture Linter

import ast
import json
from pathlib import Path
from typing import Dict, List, Optional


# -----------------------------
# CONFIGURATION
# -----------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = PROJECT_ROOT / "backend_services"

ARCHITECTURE_ROOT = PROJECT_ROOT / "architecture"
SEMANTIC_MATRIX_PATH = (
    ARCHITECTURE_ROOT / "contracts" / "semantic_allow_matrix.json"
)

REPORT_DIR = PROJECT_ROOT / "architecture_reports"
REPORT_DIR.mkdir(exist_ok=True)

REPORT_FILE = REPORT_DIR / "import_violations_report.txt"
SUMMARY_FILE = REPORT_DIR / "import_violations_summary.txt"


# -----------------------------
# LOAD SEMANTIC MATRIX
# -----------------------------

def load_semantic_matrix(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(
            f"Semantic allow matrix not found at: {path}"
        )

    with path.open(encoding="utf-8") as f:
        return json.load(f)


SEMANTIC_MATRIX = load_semantic_matrix(SEMANTIC_MATRIX_PATH)
ROLE_MAP = SEMANTIC_MATRIX["roles"]
ALLOW_MATRIX = SEMANTIC_MATRIX["allow_matrix"]


# -----------------------------
# FILE & IMPORT DISCOVERY
# -----------------------------

def discover_python_files(root: Path) -> List[Path]:
    return [p for p in root.rglob("*.py") if p.is_file()]


def detect_layer(file_path: Path) -> Optional[str]:
    """
    Determine which backend layer this file belongs to
    based on directory names.
    """
    for part in file_path.parts:
        if part in ROLE_MAP:
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
        if part in ROLE_MAP:
            return part
    return None


# -----------------------------
# SEMANTIC RULE ENGINE
# -----------------------------

def is_import_allowed(from_layer: str, to_layer: str) -> bool:
    from_role = ROLE_MAP[from_layer]
    to_role = ROLE_MAP[to_layer]

    allowed_targets = ALLOW_MATRIX.get(from_role, [])
    return to_role in allowed_targets


# -----------------------------
# LINT ENGINE
# -----------------------------

def lint() -> Dict:
    violations = []
    checked_files = 0

    for file_path in discover_python_files(BACKEND_ROOT):
        checked_files += 1

        source_layer = detect_layer(file_path)
        if not source_layer:
            continue

        imports = extract_imports(file_path)

        for imp in imports:
            target_layer = infer_import_layer(imp)

            if not target_layer or target_layer == source_layer:
                continue

            if not is_import_allowed(source_layer, target_layer):
                violations.append({
                    "file": str(file_path),
                    "from_layer": source_layer,
                    "from_role": ROLE_MAP[source_layer],
                    "import": imp,
                    "to_layer": target_layer,
                    "to_role": ROLE_MAP[target_layer],
                })

    return {
        "checked_files": checked_files,
        "violations": violations,
        "roles": ROLE_MAP,
    }


# -----------------------------
# REPORTING
# -----------------------------

def write_reports(result: Dict):
    with REPORT_FILE.open("w", encoding="utf-8") as f:
        f.write("=== Semantic Architecture Import Violations ===\n\n")

        if not result["violations"]:
            f.write("✅ No semantic violations found.\n")
        else:
            for v in result["violations"]:
                f.write(
                    f"- File: {v['file']}\n"
                    f"  From: {v['from_layer']} ({v['from_role']})\n"
                    f"  Imports: {v['import']}\n"
                    f"  To: {v['to_layer']} ({v['to_role']})\n\n"
                )

    with SUMMARY_FILE.open("w", encoding="utf-8") as f:
        f.write("=== Summary ===\n\n")
        f.write(f"Checked files: {result['checked_files']}\n")
        f.write(f"Violations: {len(result['violations'])}\n")


# -----------------------------
# ENTRY
# -----------------------------

if __name__ == "__main__":
    result = lint()
    write_reports(result)

    print("✅ Role-Aware Architecture Linter completed")
    print(f"Semantic Matrix: {SEMANTIC_MATRIX_PATH}")
    print(f"Report: {REPORT_FILE}")
