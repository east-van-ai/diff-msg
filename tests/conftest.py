"""
Shared fixtures and helpers for diff_msg.cli tests.
"""

import subprocess
import sys

import pytest


@pytest.fixture
def run_cli():
    """Return a callable that invokes `python -m diff_msg.cli` via subprocess."""

    def _run_cli(args, input_text=None, cwd=None):
        return subprocess.run(
            [sys.executable, "-m", "diff_msg.cli", *args],
            input=input_text,
            capture_output=True,
            text=True,
            cwd=cwd,
            check=False,
        )

    return _run_cli
