# CareSplit

Track Dad's health and care expenses, and how much of each one is expected
to come out of your own pocket vs. be covered by insurance/Medicare. Full
specification: [docs/spec.md](docs/spec.md). Instructions for coding
agents working in this repo: [AGENTS.md](AGENTS.md).

Note: the folder on disk is named `caresplit_app` (not `CareSplit`) only to
avoid colliding with a case-insensitive Windows filesystem match against a
sibling project elsewhere in this repo — the application itself is
CareSplit throughout the code, UI, and docs.

## Layout

```
backend/       caresplit_backend — domain types + services layer, and its tests
frontend/      caresplit_frontend — the NiceGUI UI, and its tests
docs/          spec.md and other supporting documentation
AGENTS.md      instructions for coding agents
openapi.yaml   the REST contract a real, network-separated backend would serve
pyproject.toml the uv workspace root (backend + frontend are its members)
uv.lock        locked, resolved versions for the whole workspace
```

`backend` and `frontend` are separate folders but not yet separate
*services* — the frontend imports the backend package directly, in-process.
See [AGENTS.md](AGENTS.md) for details on that distinction, and why
`openapi.yaml` doesn't have a live server behind it yet.

Every backend call the UI makes goes through one services layer
(`CareSplitService`, `backend/caresplit_backend/services/base.py`). The
only implementation today is an in-memory mock, seeded with starter
categories — **the whole app runs with no database and no backend to
stand up.**

## Running locally

Managed with [uv](https://docs.astral.sh/uv/) — `backend` and `frontend`
are members of one uv workspace, sharing a single `.venv` and lockfile at
the repo root.

```
uv sync
uv run python frontend/main.py
```

Then open http://localhost:8080/. To add a dependency to one member, run
`uv add <package>` from inside `backend/` or `frontend/` (or
`uv add --package caresplit-frontend <package>` from the root).

## Tests

```
uv run pytest
```

32 tests: pure unit tests of the split math and the mock service
(`backend/tests/`), plus headless UI tests via `nicegui.testing.User`
that click through the dashboard, expenses, and categories pages against
the mock service (`frontend/tests/`) — no browser, no backend required.

## Status

v1, mock-backed, local only. See [docs/spec.md](docs/spec.md) for full
scope and what's deliberately deferred (multi-user login, settle-up
tracking, export).
