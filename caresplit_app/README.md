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
frontend/      caresplit_frontend — the NiceGUI UI, and its tests
docs/          spec.md and other supporting documentation
AGENTS.md      instructions for coding agents
openapi.yaml   the REST contract — implemented by backend/caresplit_backend/api/
pyproject.toml the uv workspace root (backend + frontend are its members)
uv.lock        locked, resolved versions for the whole workspace
```

The FastAPI app is real and tested, but the frontend doesn't call it yet —
it still talks to the services layer in-process. See [AGENTS.md](AGENTS.md)
for that distinction in more detail.

Every backend call the UI makes goes through one services layer
(`CareSplitService`, `backend/caresplit_backend/services/base.py`). The
only implementation is an in-memory mock, seeded with starter categories —
**the whole app runs with no database, and no backend process needs to be
started, for the frontend to work.**

## The API

```
uv run uvicorn caresplit_backend.api.main:app --app-dir backend --reload
```

Then open http://localhost:8000/docs for interactive docs, or:

```
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "cindy", "password": "caresplit-demo"}'
```

to get a bearer token (demo credentials — see
`backend/caresplit_backend/api/store.py`), then send it back as
`Authorization: Bearer <accessToken>` on every other endpoint. Seeded with
a handful of sample expenses so `/dashboard` and `/reports/*` aren't empty
on first run.

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

65 tests: unit tests of the split math and the mock service, FastAPI
endpoint tests (auth, categories, expenses, dashboard, reports — via
`fastapi.testclient.TestClient`, no server process needed) in
`backend/tests/`, plus headless UI tests via `nicegui.testing.User` that
click through the dashboard, expenses, and categories pages against the
mock service in `frontend/tests/` — no browser, no live backend required
for any of it.

## Status

v1. Frontend and the mock service layer are what actually runs the app
day to day; the FastAPI backend in `backend/caresplit_backend/api/` is a
complete, independently-tested implementation of `openapi.yaml` that
nothing calls yet. See [docs/spec.md](docs/spec.md) for full product scope
and what's deliberately deferred (multi-user accounts beyond the single
seeded login, settle-up tracking, export).
