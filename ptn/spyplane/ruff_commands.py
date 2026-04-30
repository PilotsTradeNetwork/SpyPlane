#!/usr/bin/env python3
"""
Ruff and test command wrappers for the SpyPlane project.
"""

import subprocess
import sys
from pathlib import Path


def run_ruff_command(args):
    """Run ruff with the given arguments."""
    try:
        result = subprocess.run(["ruff", *args], cwd=Path.cwd(), check=False)  # noqa: S603,S607
        sys.exit(result.returncode)
    except FileNotFoundError:
        print("Error: ruff not found. Please install it with: uv sync --extra dev")
        sys.exit(1)


def lint():
    """Run ruff check."""
    run_ruff_command(["check", "."])


def format_code():
    """Run ruff format."""
    run_ruff_command(["format", "."])


def lint_fix():
    """Run ruff check --fix."""
    run_ruff_command(["check", "--fix", "."])


def run_tests():
    """Recreate the test DB then run the full unittest suite."""
    root = Path.cwd()
    recreate = root / "db" / "test_recreate.sh"
    try:
        result = subprocess.run(["bash", str(recreate)], cwd=root, check=False)  # noqa: S603,S607
        if result.returncode != 0:
            sys.exit(result.returncode)
    except FileNotFoundError:
        print("Error: bash not found.")
        sys.exit(1)
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "unittest", "discover", "tests", "-v"],
        cwd=root,
        check=False,
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ruff_commands.py <command>")
        print("Commands: lint, format, lint-fix")
        sys.exit(1)

    command = sys.argv[1]
    if command == "lint":
        lint()
    elif command == "format":
        format_code()
    elif command == "lint-fix":
        lint_fix()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
