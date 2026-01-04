# audit_project_structure.py

import os

# ===============================
# CONFIGURATION
# ===============================

PROJECT_ROOT = "."  # GreenStream root
OUTPUT_FILE = "project_structure_audit.txt"

EXCLUDED_DIRS = {
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    "venv",
    "env",
    ".env",
    "node_modules",
    "dist",
    "build",
    ".pytest_cache",
}

EXCLUDED_FILES = {
    ".DS_Store",
}

# ===============================
# CORE LOGIC
# ===============================

def should_exclude_dir(dirname: str) -> bool:
    return dirname in EXCLUDED_DIRS or dirname.startswith(".")


def should_exclude_file(filename: str) -> bool:
    return filename in EXCLUDED_FILES or filename.startswith(".")


def walk_directory(root_path, indent=0, lines=None):
    if lines is None:
        lines = []

    try:
        entries = sorted(os.listdir(root_path))
    except PermissionError:
        lines.append(" " * indent + "❌ [Permission Denied]")
        return lines

    for entry in entries:
        full_path = os.path.join(root_path, entry)

        if os.path.isdir(full_path):
            if should_exclude_dir(entry):
                continue

            lines.append(" " * indent + f"📁 {entry}/")
            walk_directory(full_path, indent + 4, lines)

        else:
            if should_exclude_file(entry):
                continue

            lines.append(" " * indent + f"📄 {entry}")

    return lines


def generate_report():
    header = [
        "GREENSTREAM PROJECT STRUCTURE AUDIT",
        "=" * 40,
        f"Root Directory: {os.path.abspath(PROJECT_ROOT)}",
        "",
    ]

    structure_lines = walk_directory(PROJECT_ROOT)

    return header + structure_lines


# ===============================
# EXECUTION
# ===============================

if __name__ == "__main__":
    report = generate_report()
    output_text = "\n".join(report)

    # Print to console
    print(output_text)

    # Write to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(output_text)

    print("\n✅ Project structure audit completed.")
    print(f"📄 Output saved to: {OUTPUT_FILE}")
