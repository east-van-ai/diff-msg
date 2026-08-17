# diff-msg

A lightweight CLI tool that generates conventional commit messages from
`git diff` output using a local LLM.

## Why

You commit `wip` like a normal person, but squash merge deserves better.
Ask `diff-msg` and get a clean conventional commit message, ready to paste.

## Overview

`diff-msg` pipes your branch diff into a locally running LLM via Ollama
and returns one formatted commit title. No internet required, no API keys.

## Usage

```bash
diff-msg --ask
```

`diff-msg` calls `git diff main...` itself and prints one commit title.
Bare `diff-msg` prints the usage banner; the generation is an explicit
`--ask`.

example output:

```text
refactor: simplify conversion logic and clean up comments
```

## Requirements

- [Ollama](https://ollama.com) running locally

## Setup

```bash
ollama pull qwen2.5-coder:3b
```

## Install

- Python 3.9 or newer
- pipx

```bash
pipx install "git+https://github.com/east-van-ai/diff-msg.git@stable"
```

## Model

default: `qwen2.5-coder:3b` (Apache 2.0)

## Privacy

Runs entirely on your machine. Your code never leaves it.
No API keys. No cloud. Nothing for your manager to worry about.

## Use of AI

This project is built with Artificial Intelligence (AI), deliberately
and in the open. Code and documentation are written in collaboration
with remote and local AI; design decisions, code review, and final
judgment stay human.

---

**East Van AI** · AI for the rest of us! · Vancouver, BC, Canada

[github.com/east-van-ai](https://github.com/east-van-ai) · <east-van-ai@proton.me>

Copyright (c) 2026 Go Nakamaru
