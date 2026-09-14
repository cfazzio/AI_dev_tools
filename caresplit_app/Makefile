.PHONY: help sync frontend backend test clean

help:
	@echo "Available targets:"
	@echo "  make sync      Install/update dependencies (uv sync)"
	@echo "  make frontend  Run the NiceGUI frontend on http://localhost:8080"
	@echo "  make backend   Run the FastAPI backend on http://localhost:8000 (docs at /docs)"
	@echo "  make test      Run the full test suite"
	@echo "  make clean     Remove __pycache__, .pytest_cache, and egg-info directories"

sync:
	uv sync

frontend:
	uv run python frontend/main.py

backend:
	uv run uvicorn caresplit_backend.api.main:app --app-dir backend --reload

test:
	uv run pytest

clean:
	find . \( -name "__pycache__" -o -name "*.egg-info" -o -name ".pytest_cache" \) -not -path "./.venv/*" -exec rm -rf {} +
