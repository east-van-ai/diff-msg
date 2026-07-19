"""
Shared fixtures and helpers for diffmsg.cli tests.
"""

import subprocess
import sys

import pytest


@pytest.fixture
def run_cli():
    """Return a callable that invokes `python -m diffmsg.cli` via subprocess."""

    def _run_cli(args, input_text=None, cwd=None):
        return subprocess.run(
            [sys.executable, "-m", "diffmsg.cli", *args],
            input=input_text,
            capture_output=True,
            text=True,
            cwd=cwd,
        )

    return _run_cli
