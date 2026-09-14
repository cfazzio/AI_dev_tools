.PHONY: help sync frontend frontend-mock backend test clean

help:
	@echo "Available targets:"
	@echo "  make sync           Install/update dependencies (uv sync)"
	@echo "  make backend        Run the FastAPI backend on http://localhost:8000 (docs at /docs)"
	@echo "  make frontend       Run the NiceGUI frontend on http://localhost:8080 (needs backend running)"
	@echo "  make frontend-mock  Run the frontend alone, against the in-process mock (no backend needed)"
	@echo "  make test           Run the full test suite (never needs a live server)"
	@echo "  make clean          Remove __pycache__, .pytest_cache, and egg-info directories"

sync:
	uv sync

backend:
	uv run uvicorn caresplit_backend.api.main:app --app-dir backend --reload

frontend:
	uv run python frontend/main.py

frontend-mock:
	CARESPLIT_BACKEND=mock uv run python frontend/main.py

test:
	uv run pytest

clean:
	find . \( -name "__pycache__" -o -name "*.egg-info" -o -name ".pytest_cache" \) -not -path "./.venv/*" -exec rm -rf {} +
