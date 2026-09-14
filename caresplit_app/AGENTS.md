# AGENTS.md

Instructions for coding agents working in this repo.

## Layout

```
backend/    Python package `caresplit_backend` (domain types + services layer) and its tests
frontend/   NiceGUI app `caresplit_frontend` (UI) and its tests
docs/       supporting documentation, incl. spec.md (the product/architecture spec)
openapi.yaml  the API contract a real, network-separated backend would serve (aspirational — see below)
```

## Current architecture (important: read before assuming a network boundary)

`/backend` and `/frontend` are separate folders but **not yet separate
services**. `frontend` imports `caresplit_backend` directly, in-process —
there is no HTTP call between them today, and `openapi.yaml` is not
implemented by anything. It documents the REST shape a real backend would
expose later, matching the `CareSplitService` protocol
(`backend/caresplit_backend/services/base.py`), so the two sides could be
built independently once/if that split happens. Do not assume the API is
live; check `backend/caresplit_backend/services/mock_service.py` for what
actually runs today.

All business logic and data access goes through `CareSplitService`. UI code
must never touch storage directly — always call
`caresplit_backend.services.get_service()`. The only implementation right
now is `MockCareSplitService`, in-memory, seeded with starter categories.
This is intentional: the whole app must run with no database and no
external service.

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
plugin). `backend/tests` covers the domain math and the mock service in
isolation; `frontend/tests/test_ui.py` drives real pages/dialogs through
`nicegui.testing.User` against the mock service, no browser needed.

Every test gets a fresh, freshly-seeded `MockCareSplitService` via the
autouse `fresh_mock_service` fixture in the root `conftest.py` — don't
assume state persists between tests.

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
