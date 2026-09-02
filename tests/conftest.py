"""
Shared fixtures and helpers for diff_msg tests.
"""

import subprocess
import sys

import pytest

from diff_msg import cli


@pytest.fixture
def run_cli():
    """Return a callable that invokes `python -m diff_msg.cli` via subprocess.

    stdin is /dev/null unless input_text is passed, so a test states whether
    it is piping instead of inheriting whatever was attached to the run.
    """

    def _run_cli(args, input_text=None, cwd=None):
        stdin = {"stdin": subprocess.DEVNULL} if input_text is None else {}
        return subprocess.run(
            [sys.executable, "-m", "diff_msg.cli", *args],
            input=input_text,
            capture_output=True,
            text=True,
            cwd=cwd,
            check=False,
            **stdin,
        )

    return _run_cli


@pytest.fixture
def call_main(monkeypatch):
    """Return a callable that runs main() on argv and hands back its code.

    Exit codes arrive two ways: returned from main, or unwound as a
    SystemExit from argparse and the version action. Both collapse here, so
    every test compares the same thing.
    """

    def _call_main(argv):
        monkeypatch.setattr("sys.argv", ["diff-msg", *argv])
        try:
            return cli.main()
        except SystemExit as exit_:
            return exit_.code

    return _call_main
