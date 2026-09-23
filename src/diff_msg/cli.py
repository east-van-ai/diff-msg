"""
# ==============================================
# East Van AI -- AI for the rest of us!
# https://github.com/east-van-ai/diff-msg
# contact: east-van-ai@proton.me
# ==============================================
#
# ~~~ ~~~ ~~~ ~~~ ~~~ ~~~ ~~~ ~~~ diff-msg ~~~ ~~~ ~~~ ~~~ ~~~ ~~~ ~~~ ~~~
#
# Suggest five commit titles for a branch by feeding `git diff main...` to a
# locally running Ollama model. No cloud calls, no API keys -- everything
# talks to localhost:11434, and your code never leaves the machine.
#
# diff-msg does not write the commit message for you. It offers five
# suggestions, and five more every time it is asked again.
#
# Usage:
#    ASK
#       diff-msg ask PATH   Suggest five commit titles for the checkout
#                           at PATH. `.` is the current directory
#       diff-msg ask        Explain the ask command
#
#    diff-msg               Print this help
#
# diff-msg reads no piped input. PATH says which repository to read.
#
# Requires: Ollama running locally with tiny-aya-global pulled
# (`ollama pull hf.co/CohereLabs/tiny-aya-global-GGUF:Q4_K_M`).
#
# Exit codes:
#    0: success (suggestions printed, nothing to commit, or documentation
#        printed)
#    1: any diff-msg-raised error (usage, a PATH that is not a directory, a
#        git failure, unreachable Ollama, unusable reply)
#    2: argparse's own errors
#
# License: MIT
# ==============================================
"""

import os
import stat
import sys
from collections import namedtuple

from diff_msg import args, cli_ask, errors

# 2 never returns through main(). Argparse's own ArgumentParser.error() and
# the version action both call sys.exit() and unwind past it.
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_ARGPARSE = 2

__all__ = ["EXIT_ARGPARSE", "EXIT_ERROR", "EXIT_OK", "main"]

Command = namedtuple("Command", "bare usage slots action")
"""A command word's answer to being typed alone, its usage line, the path slots it
reads, and the action a full invocation runs.

`bare` returns the text for the bare word; `action` runs the command. For `version`,
both read from `version_line`, since running the command answers the bare word.
"""


COMMANDS = {
    "ask": Command(
        lambda: cli_ask.__doc__,
        cli_ask.USAGE,
        cli_ask.SLOTS,
        lambda paths: cli_ask.run(*paths),
    ),
    "version": Command(
        args.version_line,
        "diff-msg version",
        (),
        lambda paths: print(args.version_line()),
    ),
}


def leading_paths(tokens):
    """Return the tokens ahead of the first flag."""
    paths = []
    for token in tokens:
        if token.startswith("-"):
            break
        paths.append(token)
    return paths


def piped_stdin():
    """Return True when stdin carries content the user sent.

    Deliberately narrower than `not isatty()`, which is also false for the
    /dev/null that cron, nohup, and CI hand a process.
    """
    if sys.stdin is None:
        return False
    try:
        if sys.stdin.isatty():
            return False
        mode = os.fstat(sys.stdin.fileno()).st_mode
    except (AttributeError, OSError, ValueError):
        return False
    return stat.S_ISFIFO(mode) or stat.S_ISREG(mode) or stat.S_ISSOCK(mode)


def usage_error(usage, message):
    """Report a command line the tool could not read, with the matching usage."""
    print(f"diff-msg: {message}", file=sys.stderr)
    print(f"Usage: {usage}", file=sys.stderr)
    return EXIT_ERROR


def readiness_error(message):
    """Report what the run needed and did not find, with no usage line."""
    sys.stdout.flush()
    print(f"diff-msg: {message}", file=sys.stderr)
    return EXIT_ERROR


def runtime_error(message):
    """Report an answer the run could not use, with no usage line."""
    sys.stdout.flush()
    print(f"diff-msg: {message}", file=sys.stderr)
    return EXIT_ERROR


def main(argv=None):
    """Parse arguments, run the matching command, return an exit code."""
    tokens = list(sys.argv[1:] if argv is None else argv)

    # ask is the only command that reads input, so its usage answers all but version.
    if piped_stdin():
        word = tokens[0] if tokens else None
        usage = COMMANDS[word].usage if word in COMMANDS else cli_ask.USAGE
        return usage_error(usage, "diff-msg reads no piped input")

    if not tokens:
        print(__doc__)
        return EXIT_OK

    # A command word and nothing else is a question, and its own docs answer.
    if len(tokens) == 1 and tokens[0] in COMMANDS:
        print(COMMANDS[tokens[0]].bare())
        return EXIT_OK

    parser = args.build_parser()
    parsed, extras = parser.parse_known_args(tokens)

    if any(extra.startswith("-") for extra in extras):
        parser.parse_args(tokens)  # argparse names the flag better, exit 2

    paths = leading_paths(tokens[1:])

    command = COMMANDS[parsed.command]

    if len(paths) < len(command.slots):
        needed = " and ".join(command.slots)
        if len(command.slots) > 1:
            needed = f"both {needed}"
        return usage_error(command.usage, f"{parsed.command} needs {needed}")

    if len(paths) > len(command.slots):
        stray = paths[len(command.slots)]
        last = command.slots[-1] if command.slots else "it"
        return usage_error(
            command.usage,
            f"{parsed.command} takes nothing after {last}: {stray!r}",
        )

    try:
        command.action(paths)
    except errors.ReadinessError as failure:
        return readiness_error(str(failure))
    except errors.RuntimeFailure as failure:
        return runtime_error(str(failure))

    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
