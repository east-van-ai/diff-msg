"""
Behaviour behind the grammar: what `ask` does once the command line has
been read. None of these require a running Ollama. The grammar itself is
pinned in test_grammar.py.
"""

import subprocess

from diff_msg import args, cli_ask

# ---------- ask, without a model ----------


def test_ask_with_no_diff_exits_clean(call_main, capsys, monkeypatch, tmp_path):
    """An empty diff reports no changes and never contacts the model."""
    monkeypatch.setattr(cli_ask, "get_branch", lambda _cwd: "feat/x")
    monkeypatch.setattr(cli_ask, "get_diff", lambda _cwd: "")
    assert call_main(["ask", str(tmp_path)]) == 0
    assert "No changes vs main." in capsys.readouterr().out


def test_ask_reads_the_repository_it_was_pointed_at(call_main, monkeypatch, tmp_path):
    """PATH reaches git as its working directory, not the process's own."""
    seen = []
    monkeypatch.setattr(cli_ask, "get_branch", lambda cwd: seen.append(cwd) or "main")
    monkeypatch.setattr(cli_ask, "get_diff", lambda cwd: seen.append(cwd) or "")
    call_main(["ask", str(tmp_path)])
    assert seen == [str(tmp_path), str(tmp_path)]


# ---------- version ----------


def test_version_falls_back_when_not_installed(monkeypatch):
    """An uninstalled distribution reports a placeholder rather than raising."""

    def _missing(_name):
        raise args.metadata.PackageNotFoundError

    monkeypatch.setattr(args.metadata, "version", _missing)
    assert args.installed_version() == "unknown (not installed)"


# ---------- git failures ----------


def _git(argv, cwd):
    """Run a git command in cwd, failing the test if git itself fails."""
    subprocess.run(["git", *argv], cwd=cwd, check=True, capture_output=True)


def test_ask_outside_a_repository_errors(run_cli, tmp_path):
    """A directory that is not a checkout exits 1 with one `diff-msg:` prefix."""
    result = run_cli(["ask", str(tmp_path)])
    assert result.returncode == 1
    assert result.stderr.startswith("diff-msg: ")
    assert "fatal:" not in result.stderr
    assert "not a git repository" in result.stderr
    assert result.stdout == ""


def test_ask_without_a_main_branch_errors(run_cli, tmp_path):
    """A repo with no `main` branch exits 1 in git's own words."""
    _git(["init", "-q", "-b", "trunk"], cwd=tmp_path)
    result = run_cli(["ask", str(tmp_path)])
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
    result = run_cli(["ask", "."], cwd=tmp_path)
    assert result.returncode == 0
    assert "No changes vs main." in result.stdout
