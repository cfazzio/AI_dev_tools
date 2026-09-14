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
backend/       caresplit_backend — domain types, services layer, a FastAPI
               app implementing openapi.yaml, and all of that's tests
frontend/      caresplit_frontend — the NiceGUI UI, an HTTP client for the
               API, and its tests
docs/          spec.md and other supporting documentation
AGENTS.md      instructions for coding agents
openapi.yaml   the REST contract — implemented by backend/caresplit_backend/api/
pyproject.toml the uv workspace root (backend + frontend are its members)
uv.lock        locked, resolved versions for the whole workspace
```

The frontend calls the real FastAPI backend over HTTP by default (logs
in, caches a bearer token, refreshes it automatically if it expires). Set
`CARESPLIT_BACKEND=mock` to run the frontend alone against an in-process
mock instead — no backend process, no network — which is also what the
test suite does, so tests never need a live server. See
[AGENTS.md](AGENTS.md) for the full picture, including the demo login and
the other environment variables.

Every backend call the UI makes goes through one services layer
(`CareSplitService`, `backend/caresplit_backend/services/base.py`) —
either the mock or the real HTTP client satisfies it; no page knows or
cares which.

## Running locally

Managed with [uv](https://docs.astral.sh/uv/) — `backend` and `frontend`
are members of one uv workspace, sharing a single `.venv` and lockfile at
the repo root.

```
uv sync
uv run uvicorn caresplit_backend.api.main:app --app-dir backend --reload   # http://localhost:8000
uv run python frontend/main.py                                             # http://localhost:8080
```

Start the backend first — the frontend logs in on first use and errors if
it can't reach it. Interactive API docs at http://localhost:8000/docs;
demo login `cindy` / `caresplit-demo` (see
`backend/caresplit_backend/api/store.py`), seeded with a handful of sample
expenses so the dashboard and reports aren't empty on first run.

To run the frontend alone, no backend needed:
```
CARESPLIT_BACKEND=mock uv run python frontend/main.py
```

To add a dependency to one workspace member, run `uv add <package>` from
inside `backend/` or `frontend/` (or `uv add --package caresplit-frontend
<package>` from the root).

## Tests

```
uv run pytest
```

75 tests, none needing a live server: unit tests of the split math and the
mock service, FastAPI endpoint tests (auth, categories, expenses,
dashboard, reports) in `backend/tests/`; headless UI tests via
`nicegui.testing.User` (forced to the mock) plus integration tests of the
real HTTP client against the real FastAPI app (via a throwaway local
server started for the test run) in `frontend/tests/`.

## Status

v1. The frontend talks to the real backend by default now — both need to
be running for the full experience, or run the frontend alone against the
mock for quick local UI work. See [docs/spec.md](docs/spec.md) for full
product scope and what's deliberately deferred (multi-user accounts beyond
the single seeded login, settle-up tracking, export).
