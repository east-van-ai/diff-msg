# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [0.4.0] - 2026-08-17

### Added

- a JSON schema on the Ollama request pins the reply to exactly five items,
  each capped at 100 characters
- a reply that escapes the schema exits 1 as `diff-msg: the model returned an
  unusable reply`

### Changed

- `--ask` prints five numbered suggestions instead of one commit title
- the prompt no longer asks for Conventional Commit format. A suggestion is a
  plain sentence, with no prefix, no scope, and no casing rule
- suggestions are no longer reproducible. Sampling runs at temperature 0.8
  with no seed, so asking again gives a different set

## [0.3.0] - 2026-08-17

### Changed

- renamed the project from `diffmsg` to `diff-msg`: distribution name and
  console script are now `diff-msg`, the importable package moved from
  `src/diffmsg/` to `src/diff_msg/` (Python module names can't contain
  hyphens), and all docs/tests updated to match
- tightened the prompt rules: `style` dropped from the allowed prefixes, and
  the model is now told to use Conventional Commit format without a scope and
  to never wrap the title in code fences

### Removed

- `requirements.txt` and `requirements-dev.txt`. `pyproject.toml` is now the
  only place dependencies are declared, with the dev tools in a `dev`
  dependency group (`pip install -e . --group dev`)

### Fixed

- git failures no longer masquerade as an empty diff. No repository, or no
  `main` branch to diff against, now exits 1 with git's own message behind the
  `diff-msg:` prefix instead of reporting "No changes vs main." and exiting 0

## [0.2.0] - 2026-07-19

### Added

- src layout (`src/diffmsg/cli.py`), `pyproject.toml` packaging, and a
  `diffmsg` console script installable with pipx
- CLI grammar: bare `diffmsg` on a TTY prints the usage banner and exits
  0; generating a title is the explicit `diffmsg --ask`; bare with piped
  stdin is a usage error; errors go to stderr as `diffmsg: ...`; exit
  codes 0/1/2
- an unreachable Ollama is now a clean `diffmsg: cannot reach Ollama ...`
  error (exit 1) instead of a raw requests traceback
- pytest suite (prompt unit tests + CLI grammar tests), none requiring a
  running Ollama
- DESIGN.md, RELEASING.md, requirements-dev.txt

### Changed

- requirements.txt trimmed to runtime deps only (`requests`); `black`
  moved to requirements-dev.txt; unused `ollama` package dropped

### Removed

- top-level `diffmsg.py` (moved to `src/diffmsg/cli.py`)
