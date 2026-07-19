# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [v0.2.0] - 2026-07-19

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
