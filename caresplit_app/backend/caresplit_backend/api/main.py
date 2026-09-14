"""The CareSplit FastAPI app. Run with:

    uv run uvicorn caresplit_backend.api.main:app --reload

Implements openapi.yaml. The store (categories, expenses, users) is an
in-memory singleton seeded on import — see store.py — so every fresh
process starts with the same demo data and the same demo login.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from caresplit_backend.api.models import Error
from caresplit_backend.api.routers import auth, categories, dashboard, expenses, reports
from caresplit_backend.services.errors import CategoryInUseError, DuplicateCategoryError, NotFoundError

app = FastAPI(title="CareSplit API", version="0.2.0")

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(expenses.router)
app.include_router(dashboard.router)
app.include_router(reports.router)


def _error(message: str) -> dict:
    return Error(message=message).model_dump(by_alias=True)


def _not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content=_error(str(exc)))


def _conflict_handler(
    request: Request, exc: DuplicateCategoryError | CategoryInUseError
) -> JSONResponse:
    return JSONResponse(status_code=409, content=_error(str(exc)))


def _http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    # Overrides FastAPI's default {"detail": ...} body (used for the 401s
    # raised in auth.py and routers/auth.py) so every error response,
    # regardless of where it's raised from, matches the Error schema.
    return JSONResponse(
        status_code=exc.status_code, content=_error(str(exc.detail)), headers=exc.headers
    )


app.add_exception_handler(NotFoundError, _not_found_handler)
app.add_exception_handler(DuplicateCategoryError, _conflict_handler)
app.add_exception_handler(CategoryInUseError, _conflict_handler)
app.add_exception_handler(HTTPException, _http_exception_handler)
