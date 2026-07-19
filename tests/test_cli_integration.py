"""
CLI grammar tests. None of these require a running Ollama.
"""

import pytest

from diffmsg import cli

# ---------- bare invocation ----------


def test_bare_on_tty_prints_banner(monkeypatch, capsys):
    """Bare `diffmsg` on a TTY prints the usage banner and exits 0."""
    monkeypatch.setattr("sys.argv", ["diffmsg"])
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    with pytest.raises(SystemExit) as excinfo:
        cli.main()
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    assert "diffmsg" in out
    assert "--ask" in out


def test_bare_with_piped_stdin_is_usage_error(run_cli):
    """Bare `diffmsg` with piped stdin errors to stderr with exit 1."""
    result = run_cli([], input_text="")
    assert result.returncode == 1
    assert "diffmsg:" in result.stderr
    assert "Usage: diffmsg" in result.stderr
    assert result.stdout == ""


# ---------- argparse convention ----------


def test_unknown_flag_is_argparse_error(run_cli):
    """An unknown flag is argparse's own error: exit 2."""
    result = run_cli(["--nope"])
    assert result.returncode == 2


# ---------- --ask without a model ----------


def test_ask_with_no_diff_exits_clean(monkeypatch, capsys):
    """`--ask` with an empty diff reports no changes and exits 0."""
    monkeypatch.setattr("sys.argv", ["diffmsg", "--ask"])
    monkeypatch.setattr(cli, "get_branch", lambda: "feat/x")
    monkeypatch.setattr(cli, "get_diff", lambda: "")
    with pytest.raises(SystemExit) as excinfo:
        cli.main()
    assert excinfo.value.code == 0
    assert "No changes vs main." in capsys.readouterr().out
