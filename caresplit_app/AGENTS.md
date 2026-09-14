# AGENTS.md

Instructions for coding agents working in this repo.

## Layout

```
backend/    Python package `caresplit_backend`: domain types, services layer,
            and a FastAPI app (caresplit_backend/api/) implementing openapi.yaml.
            Its tests too.
frontend/   NiceGUI app `caresplit_frontend` (UI) and its tests
docs/       supporting documentation, incl. spec.md (the product/architecture spec)
openapi.yaml  the API contract — implemented by backend/caresplit_backend/api/ (see below)
```

## Current architecture (important: read before assuming a network boundary)

`frontend` still imports `caresplit_backend` directly, in-process — there
is **no HTTP call between frontend and backend today.** `openapi.yaml` is
implemented (`backend/caresplit_backend/api/`, a real runnable FastAPI
app, tested independently in `backend/tests/test_api_*.py`), but nothing
currently wires the frontend to call it over the network. If asked to make
the frontend actually use the API, that means adding an HTTP-backed
`CareSplitService` implementation in `frontend/` (an "ApiCareSplitService")
plus a place to store the bearer token client-side — it does not exist
yet. Don't assume it's wired up; check `frontend/caresplit_frontend/pages/*.py`
for what actually runs (still calling `caresplit_backend.services.get_service()`
directly).

All business logic and data access goes through `CareSplitService`
(`backend/caresplit_backend/services/base.py`), a Protocol. UI code (and
the FastAPI routers) must never touch storage directly — always call
`caresplit_backend.services.get_service()` (in-process) or, inside the API
layer, `caresplit_backend.api.store.get_store().expenses` (same
`MockCareSplitService`, separately instantiated — the two are independent
singletons, not shared state). The only implementation is
`MockCareSplitService`, in-memory, seeded with starter categories. This is
intentional: the whole app, and the API on its own, must run with no
database and no external service.

### The API layer (`backend/caresplit_backend/api/`)

```
main.py            FastAPI() app, router registration, exception handlers
models.py          Pydantic request/response schemas (camelCase, Decimal-as-string)
store.py           in-memory store: wraps MockCareSplitService + user records; seeds demo data
auth.py            password hashing (PBKDF2-HMAC-SHA256) + opaque bearer tokens
routers/           one module per resource (auth, categories, expenses, dashboard, reports)
```

Run it: `uv run uvicorn caresplit_backend.api.main:app --app-dir backend --reload`
(or from inside `backend/`, drop `--app-dir`). Demo login:
`caresplit_backend.api.store.DEMO_USERNAME` / `DEMO_PASSWORD` — every
endpoint except `POST /auth/token` requires
`Authorization: Bearer <token>` from that login. Interactive docs at
`/docs` once running.

Every operation's error responses are matched exactly to what
`MockCareSplitService` raises (`NotFoundError` -> 404, `DuplicateCategoryError`/
`CategoryInUseError` -> 409, both via `main.py`'s exception handlers) and to
FastAPI's own `HTTPException` (401s from `auth.py`) — the latter needed its
own handler too, since FastAPI's default `HTTPException` body is
`{"detail": ...}`, not the `{"message": ...}` the spec's `Error` schema
requires. If you add a new error case, make sure its response body still
matches `Error`, and add a test asserting the actual JSON shape, not just
the status code — that mismatch is exactly what slipped through until a
test checked the body.

## Setup

Managed with [uv](https://docs.astral.sh/uv/). `backend` and `frontend`
are members of one uv workspace (`pyproject.toml` + `uv.lock` at the repo
root) sharing a single `.venv`. `frontend`'s dependency on
`caresplit-backend` is declared as a workspace source
(`frontend/pyproject.toml`'s `[tool.uv.sources]`), so `uv sync` installs it
editable automatically — that's what makes `import caresplit_backend` work
from `frontend/` with no path hacks.

```
uv sync
```

To add a dependency: `uv add <package>` from inside `backend/` or
`frontend/` (uv resolves against the nearest pyproject.toml). Don't hand-edit
`uv.lock`; let `uv add`/`uv sync` regenerate it, and commit the lockfile
alongside the pyproject.toml change.

## Running

```
uv run python frontend/main.py
```
Opens on http://localhost:8080/.

## Tests

```
uv run pytest
```
Runs both `backend/tests` and `frontend/tests` (see `pytest.ini` at the
root — it sets `pythonpath = frontend` so `caresplit_frontend` is
importable during collection, and registers NiceGUI's headless UI-testing
plugin). `backend/tests/test_domain.py` and `test_mock_service.py` cover
the domain math and the mock service in isolation; `test_api_*.py` drive
the FastAPI app through `fastapi.testclient.TestClient` (see
`backend/tests/conftest.py` for the `client`/`auth_headers` fixtures);
`frontend/tests/test_ui.py` drives real pages/dialogs through
`nicegui.testing.User` against the mock service, no browser needed.

Two independent autouse reset fixtures exist — don't assume state persists
between tests, and don't assume resetting one resets the other:
- root `conftest.py`: `fresh_mock_service` resets the frontend-facing
  `caresplit_backend.services.get_service()` singleton.
- `backend/tests/conftest.py`: `_reset_api_state` resets the API's own
  `caresplit_backend.api.store` singleton and clears issued tokens.

## Conventions

- No comments explaining *what* code does — only *why*, and only when
  non-obvious (see existing files for the tone).
- New backend-visible behavior goes through `CareSplitService`
  (`backend/caresplit_backend/services/base.py`) first, then
  `MockCareSplitService`, then the UI. Don't let a page reach past the
  service layer.
- Money and percentages are `Decimal`, never `float`, in
  `caresplit_backend`. The one place floats appear is NiceGUI's
  `ui.number` widgets on the frontend; convert via `Decimal(str(value))`
  immediately, and use `caresplit_frontend.components.format_pct` for
  displaying a percent (plain `:g` formatting on a `Decimal` keeps
  spurious trailing zeros — don't reintroduce that bug).
- Interactive elements that UI tests need to target should get a
  `.mark("some-name")` call (see existing pages for the naming pattern:
  `<page>-<field>`, `<page>-row-<id>`).
- Update `docs/spec.md` when product scope changes, not just the code.
- Commit regularly — small, working increments (e.g. "add category delete
  protection", "restructure into backend/frontend") rather than one large
  commit at the end of a session.
