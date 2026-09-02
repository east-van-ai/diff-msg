"""
The accepted command line, pinned. A grammar that drifts still parses, it
just means something else, so nothing else in the suite fails on its own
when the shape moves.
"""

import pytest

from diff_msg import cli, cli_ask


@pytest.fixture
def no_git(monkeypatch):
    """Fail the test if anything shells out to git."""

    def _unreachable(*_args):
        raise AssertionError("git was called")

    monkeypatch.setattr(cli_ask, "get_branch", _unreachable)
    monkeypatch.setattr(cli_ask, "get_diff", _unreachable)


# ---------- bare words are questions ----------


def test_bare_prints_the_banner(call_main, capsys, no_git):
    """Bare `diff-msg` prints the banner and exits 0."""
    assert call_main([]) == 0
    out = capsys.readouterr().out
    assert "diff-msg ask PATH" in out


def test_bare_ask_prints_its_own_docs(call_main, capsys, no_git):
    """`diff-msg ask` alone explains itself and exits 0."""
    assert call_main(["ask"]) == 0
    assert "diff-msg ask" in capsys.readouterr().out


def test_neither_version_spelling_is_advertised(call_main, capsys, no_git):
    """The banner documents the work, and a version number is not that."""
    call_main([])
    out = capsys.readouterr().out
    assert "--version" not in out
    assert "--ask" not in out


# ---------- ask ----------


def test_ask_with_an_unknown_flag_is_argparse_error(call_main, capsys, no_git):
    """`ask` carries no flags yet, so any flag is argparse's own: exit 2."""
    assert call_main(["ask", "--nope"]) == 2
    assert "usage" in capsys.readouterr().err.lower()


def test_ask_with_a_stray_second_word_is_an_error(call_main, capsys, no_git):
    """A bare word past PATH is diff-msg's own error, not argparse's."""
    assert call_main(["ask", ".", "extra"]) == 1
    err = capsys.readouterr().err
    assert err.startswith("diff-msg: ")
    assert "extra" in err
    assert "Usage: diff-msg ask PATH" in err


def test_ask_on_a_file_is_a_readiness_failure(call_main, capsys, tmp_path, no_git):
    """A PATH that is not a directory exits 1 and prints no usage line."""
    target = tmp_path / "a.txt"
    target.write_text("hi\n")
    assert call_main(["ask", str(target)]) == 1
    err = capsys.readouterr().err
    assert err.startswith("diff-msg: ")
    assert "Usage:" not in err


def test_leading_paths_stops_at_the_first_flag():
    """The slot reader takes the words ahead of the flags and nothing after."""
    assert cli.leading_paths([".", "--flag", "PATH"]) == ["."]
    assert cli.leading_paths(["--flag", "PATH"]) == []


# ---------- version ----------


def test_both_version_spellings_print_the_same_line(run_cli):
    """`version` and `--version` render through one helper, so they agree."""
    word = run_cli(["version"])
    flag = run_cli(["--version"])
    assert word.returncode == 0
    assert flag.returncode == 0
    assert word.stdout == flag.stdout
    assert word.stdout.startswith("diff-msg ")
    assert len(word.stdout.strip().splitlines()) == 1


def test_version_takes_no_argument(call_main, capsys, no_git):
    """`version` acts on its own, so a word after it is a stray: exit 1."""
    assert call_main(["version", "extra"]) == 1
    assert "extra" in capsys.readouterr().err


def test_version_flag_answers_before_the_command_runs(call_main, capsys, no_git):
    """The version action fires during parsing and reaches no git command."""
    assert call_main(["--version", "ask", "."]) == 0
    assert capsys.readouterr().out.startswith("diff-msg ")


# ---------- piped input ----------


def test_piped_stdin_is_a_usage_error(run_cli):
    """A diff sent down a pipe was sent to be read, so silence would lie."""
    result = run_cli(["ask", "."], input_text="a diff\n")
    assert result.returncode == 1
    assert "diff-msg:" in result.stderr
    assert "Usage: diff-msg ask PATH" in result.stderr
    assert result.stdout == ""


def test_dev_null_stdin_is_not_piped(run_cli):
    """cron and nohup hand a process /dev/null, and that is not content."""
    result = run_cli([])
    assert result.returncode == 0
    assert "diff-msg ask PATH" in result.stdout


# ---------- argparse's own ----------


def test_unknown_command_is_argparse_error(run_cli):
    """An unknown command word is argparse's own error: exit 2."""
    assert run_cli(["nope"]).returncode == 2


def test_unknown_flag_is_argparse_error(run_cli):
    """An unknown flag is argparse's own error: exit 2."""
    assert run_cli(["--nope"]).returncode == 2
