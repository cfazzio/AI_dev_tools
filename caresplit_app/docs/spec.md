# CareSplit — Specification

## Purpose

Track Dad's health and care expenses, and how much of each one is expected to
come out of your own pocket vs. be covered by insurance/Medicare. Single-user
tool: you are the only person who logs in and enters data. Not tax or
insurance advice — a record-keeping aid.

## Core concept: category-level splits

Every expense belongs to a **category** (Medical, Prescriptions, In-home
care, Transportation, ...). Each category has a default split — a percentage
that's expected to come out of your pocket ("my share"), with the remainder
attributed to insurance/Medicare ("insurance share"). Logging an expense
copies its category's default split at the time it's created; you can
override the split for that one expense (e.g. a specific bill insurance
won't touch at all) without changing the category's default for future
expenses.

## Domain model

**Category**
- `name` (unique)
- `pct_me` — default percent that's your share, 0–100
- `pct_insurance` — derived: `100 - pct_me`
- `notes` (optional free text)

**Expense**
- `date`
- `category` (reference to a Category)
- `amount` (currency, 2 decimal places)
- `description` (optional short text)
- `pct_me` — this expense's share split; defaults from the category at
  creation time, editable afterward without affecting the category
- `pct_insurance` — derived: `100 - pct_me`
- `amount_me` — derived: `amount * pct_me / 100`
- `amount_insurance` — derived: `amount - amount_me`
- `receipt` (optional attached file — photo or PDF)
- `note` (optional free text)

## Features (v1)

1. **Dashboard** — this month's and this year's totals (overall, my share,
   insurance share), plus a list of recent expenses.
2. **Expenses** — list (filterable by category), add, edit, delete. Add/edit
   captures date, category, amount, description, split override, receipt,
   note.
3. **Categories** — list, add, edit. A category can't be deleted while any
   expense still references it (protect against orphaned data).
4. **Reports** — pick a year, see totals broken down by category and by
   month (each broken into total / my share / insurance share).

### Explicitly out of scope for v1

- Multiple user accounts / login — single local user only.
- Settle-up / payment tracking between people (this app tracks an
  expected split, not a running balance between two parties who pay each
  other back).
- CSV/data export.
- Editing history / audit log.

These may be revisited later but should not block v1.

## Repo layout

```
backend/    caresplit_backend — domain types + services layer, and its tests
frontend/   caresplit_frontend — the NiceGUI UI, and its tests
docs/       this file
openapi.yaml  the REST contract a real, network-separated backend would serve
```

`backend` and `frontend` are separate folders but **not yet separate
services** — `frontend` imports `caresplit_backend` directly, in-process.
`openapi.yaml` documents the API shape for when that becomes a real network
boundary; nothing serves it yet. See `AGENTS.md` for the current-vs-future
distinction in more detail.

## Architecture

**All business logic and data access is centralized behind one services
layer** (`backend/caresplit_backend/services/`). UI code never touches
storage directly — every read or write goes through the service interface
defined in `services/base.py` (a `Protocol`):

- `list_categories()`, `create_category(...)`, `update_category(...)`,
  `delete_category(...)`
- `list_expenses(category_id=None)`, `get_expense(id)`,
  `create_expense(...)`, `update_expense(...)`, `delete_expense(...)`
- `dashboard_totals(today)`
- `available_years()`, `yearly_report(year)`

This lets the UI, and its tests, run against a **mock implementation**
(`services/mock_service.py`) that keeps everything in memory and needs no
database, network, or external service — the whole app runs standalone.
A real implementation (e.g. backed by a database, possibly behind an HTTP
API matching `openapi.yaml`) can be dropped in later by writing a second
class that satisfies the same `CareSplitService` protocol; no UI code
should need to change. Which implementation is active is chosen in one
place (`caresplit_backend/services/__init__.py:get_service`), currently
hard-wired to the mock since no real backend exists yet.

## Frontend

Python full-stack: [NiceGUI](https://nicegui.io/) for the UI (chosen over
Reflex to avoid a Node/Bun build toolchain — pure `pip install`, fast local
startup, good fit for a forms-and-tables app like this). Pages:

- `/` — Dashboard
- `/expenses` — Expense list + add/edit dialogs
- `/categories` — Category list + add/edit dialogs
- `/reports` — Year picker + category/month breakdown tables

Single persistent header/nav, no full page reloads (NiceGUI is
websocket-driven), mobile-width friendly since this will mostly be used from
a phone.

## Testing

Unit tests target the services layer (the mock implementation) directly,
independent of any UI: category/expense CRUD, split calculation (default
and override), category-in-use delete protection, dashboard and yearly
report aggregation.

## Status

v1, mock-backed, local only. Running the app requires no setup beyond the
install steps in the root `README.md` — there is no database to migrate
and no external service to configure.
