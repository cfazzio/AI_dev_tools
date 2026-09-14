# AGENTS.md

Instructions for coding agents working in this repo.

## Layout

```
backend/    Python package `caresplit_backend`: domain types, services layer,
            and a FastAPI app (caresplit_backend/api/) implementing openapi.yaml.
            Its tests too.
frontend/   NiceGUI app `caresplit_frontend` (UI), an HTTP client for the
            API (api_client.py), and its tests.
docs/       supporting documentation, incl. spec.md (the product/architecture spec)
openapi.yaml  the API contract — implemented by backend/caresplit_backend/api/ (see below)
```

## Current architecture

The frontend calls the real backend over HTTP **by default.** Every page
calls `caresplit_frontend.services.get_service()`, which by default
constructs `ApiCareSplitService` (`frontend/caresplit_frontend/api_client.py`)
— an `httpx`-based `CareSplitService` implementation that logs in (bearer
token, cached and reused, auto-refreshed on expiry) and speaks the exact
wire format in `openapi.yaml` (camelCase, decimals as strings). This means
**running the frontend for real now requires the backend to be running**
(`uv run uvicorn caresplit_backend.api.main:app --app-dir backend`) —
without it, the frontend will fail to log in on first use.

Set `CARESPLIT_BACKEND=mock` to run the frontend against the in-process
`MockCareSplitService` instead — no backend process needed. This is what
`frontend/tests/conftest.py` forces for every frontend test, so the test
suite as a whole never needs a live server. Other env vars
`ApiCareSplitService` reads: `CARESPLIT_API_URL` (default
`http://localhost:8000`), `CARESPLIT_API_USERNAME` /
`CARESPLIT_API_PASSWORD` (default to the backend's seeded demo login).

All business logic and data access goes through `CareSplitService`
(`backend/caresplit_backend/services/base.py`), a Protocol — three
implementations satisfy it: `MockCareSplitService` (in-process, backend
package), `ApiCareSplitService` (HTTP, frontend package), and the FastAPI
routers themselves call a *fourth*, separately-instantiated
`MockCareSplitService` via `caresplit_backend.api.store.get_store().expenses`
(the API's actual data store — not shared with anything else; resetting
one does not reset another). UI code and FastAPI routers must never touch
storage directly, always through one of these.

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

Two processes, both needed for the frontend to actually show data (start
the backend first — the frontend logs in on first use and will error if
it can't reach it):

```
uv run uvicorn caresplit_backend.api.main:app --app-dir backend --reload   # http://localhost:8000
uv run python frontend/main.py                                             # http://localhost:8080
```

Or `CARESPLIT_BACKEND=mock uv run python frontend/main.py` to run the
frontend alone, against the in-process mock.

## Tests

```
uv run pytest
```
No live server needed for any of it — see `pytest.ini` at the root (sets
`pythonpath = frontend`, registers NiceGUI's headless UI-testing plugin).

- `backend/tests/test_domain.py`, `test_mock_service.py` — domain math and
  the mock service, in isolation.
- `backend/tests/test_api_*.py` — the FastAPI app through
  `fastapi.testclient.TestClient` (see `backend/tests/conftest.py` for the
  `client`/`auth_headers` fixtures).
- `frontend/tests/test_ui.py` — real pages/dialogs through
  `nicegui.testing.User`. `frontend/tests/conftest.py` forces
  `CARESPLIT_BACKEND=mock`, so these run against the in-process mock, not
  the API.
- `frontend/tests/test_api_client.py` — `ApiCareSplitService` against the
  real FastAPI app, on a real (ephemeral, localhost) uvicorn server
  started in a background thread for the test module. httpx's
  `ASGITransport` doesn't work here — it's async-only, and
  `ApiCareSplitService` is deliberately sync (same calling convention as
  the mock) — hence an actual, if throwaway, server.

Two independent autouse reset fixtures live in `frontend/tests/conftest.py`
— don't assume state persists between tests, and don't assume resetting
one resets the other: `_reset_frontend_service` resets the frontend's own
`caresplit_frontend.services` singleton (forced to mock);
`_reset_backend_api_state` resets the API's `caresplit_backend.api.store`
singleton and clears issued tokens — needed for `test_api_client.py`, a
no-op for `test_ui.py`. `backend/tests/conftest.py` has its own,
independent copy of the latter for `backend/tests/test_api_*.py`.

## Conventions

- No comments explaining *what* code does — only *why*, and only when
  non-obvious (see existing files for the tone).
- New backend-visible behavior goes through `CareSplitService`
  (`backend/caresplit_backend/services/base.py`) first, then every
  implementation: `MockCareSplitService`, the API layer
  (`routers/`, `models.py`, and `openapi.yaml` itself), and
  `ApiCareSplitService` on the frontend side — then the UI. Don't let a
  page reach past the service layer, and don't add a method to the
  protocol without adding it everywhere else that must satisfy it.
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
