"""
The command line's vocabulary: the parser and the version line. Nothing
here does any work.
"""

import argparse
from importlib import metadata

from diff_msg import cli_ask

PROG = "diff-msg"
DIST = "diff-msg"


def installed_version():
    """Return the version of the installed diff-msg distribution.

    Guarded, because the parser is built on every invocation past a bare
    word: an unguarded lookup would take down every command, not just the
    two that ask for the number.
    """
    try:
        return metadata.version(DIST)
    except metadata.PackageNotFoundError:
        return "unknown (not installed)"


def version_line():
    """Return the program name and the installed version on one line."""
    return f"{PROG} {installed_version()}"


def build_parser():
    """Return the parser for the whole command surface.

    It rejects, it does not resolve: an unknown command word or an unknown
    flag is argparse's error at exit 2, while the accepted grammar is read
    off the argv slots in cli.py.
    """
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Suggest five commit titles from your branch diff.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=version_line(),
        help="print the installed version and exit",
    )

    subparsers = parser.add_subparsers(dest="command")

    # Optional, so a bare `diff-msg ask` reaches the bare-word rule in
    # cli.py rather than dying as a missing positional at exit 2.
    ask = subparsers.add_parser("ask", help=cli_ask.HELP, description=cli_ask.HELP)
    ask.add_argument("path", nargs="?", help="the git checkout to read")

    subparsers.add_parser("version", help="print the installed version")

    return parser
