"""
CLI grammar tests. None of these require a running Ollama.
"""

import subprocess

import pytest

from diff_msg import cli

# ---------- bare invocation ----------


def test_bare_on_tty_prints_banner(monkeypatch, capsys):
    """Bare `diff-msg` on a TTY prints the usage banner and exits 0."""
    monkeypatch.setattr("sys.argv", ["diff-msg"])
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    with pytest.raises(SystemExit) as excinfo:
        cli.main()
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    assert "diff-msg" in out
    assert "--ask" in out


def test_bare_with_piped_stdin_is_usage_error(run_cli):
    """Bare `diff-msg` with piped stdin errors to stderr with exit 1."""
    result = run_cli([], input_text="")
    assert result.returncode == 1
    assert "diff-msg:" in result.stderr
    assert "Usage: diff-msg" in result.stderr
    assert result.stdout == ""


# ---------- argparse convention ----------


def test_unknown_flag_is_argparse_error(run_cli):
    """An unknown flag is argparse's own error: exit 2."""
    result = run_cli(["--nope"])
    assert result.returncode == 2


# ---------- --ask without a model ----------


def test_ask_with_no_diff_exits_clean(monkeypatch, capsys):
    """`--ask` with an empty diff reports no changes and exits 0."""
    monkeypatch.setattr("sys.argv", ["diff-msg", "--ask"])
    monkeypatch.setattr(cli, "get_branch", lambda: "feat/x")
    monkeypatch.setattr(cli, "get_diff", lambda: "")
    with pytest.raises(SystemExit) as excinfo:
        cli.main()
    assert excinfo.value.code == 0
    assert "No changes vs main." in capsys.readouterr().out


# ---------- git failures ----------


def _git(args, cwd):
    """Run a git command in cwd, failing the test if git itself fails."""
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def test_ask_outside_a_repository_errors(run_cli, tmp_path):
    """`--ask` outside a repository exits 1 with a single `diff-msg:` prefix."""
    result = run_cli(["--ask"], cwd=tmp_path)
    assert result.returncode == 1
    assert result.stderr.startswith("diff-msg: ")
    assert "fatal:" not in result.stderr
    assert "not a git repository" in result.stderr
    assert result.stdout == ""


def test_ask_without_a_main_branch_errors(run_cli, tmp_path):
    """`--ask` in a repo with no `main` branch exits 1 in git's own words."""
    _git(["init", "-q", "-b", "trunk"], cwd=tmp_path)
    result = run_cli(["--ask"], cwd=tmp_path)
    assert result.returncode == 1
    assert result.stderr.startswith("diff-msg: ")
    assert "fatal:" not in result.stderr
    assert result.stdout == ""


def test_ask_on_a_detached_head_is_not_a_failure(run_cli, tmp_path):
    """A detached HEAD has no branch name, but git exits 0, so diff-msg does too."""
    _git(["init", "-q", "-b", "main"], cwd=tmp_path)
    (tmp_path / "a.txt").write_text("hi\n")
    _git(["add", "."], cwd=tmp_path)
    _git(
        ["-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "one"],
        cwd=tmp_path,
    )
    _git(["switch", "-q", "--detach", "HEAD"], cwd=tmp_path)
    result = run_cli(["--ask"], cwd=tmp_path)
    assert result.returncode == 0
    assert "No changes vs main." in result.stdout
