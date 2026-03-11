"""
GitHub state management: read/write state files and commit changes.
"""

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent


def read_state(file_path: str) -> dict:
    """Read a JSON state file from the repo."""
    full_path = REPO_ROOT / file_path
    if not full_path.exists():
        return {}
    return json.loads(full_path.read_text(encoding="utf-8"))


def write_state(file_path: str, data: dict):
    """Write a JSON state file to the repo."""
    full_path = REPO_ROOT / file_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def commit_changes(message: str):
    """Stage all changes and commit to the repo."""
    try:
        subprocess.run(
            ["git", "add", "-A"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=True,
        )

        # Check if there are changes to commit
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )

        if not result.stdout.strip():
            print("  No changes to commit.")
            return

        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=True,
        )

        subprocess.run(
            ["git", "push"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=True,
        )

        print(f"  Committed and pushed: {message}")
    except subprocess.CalledProcessError as e:
        print(f"  Git error: {e.stderr}")
