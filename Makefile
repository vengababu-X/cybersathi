# CyberSathi — root convenience targets.
#
# The backend has its own Makefile with the data/train/seed pipeline; this one is the
# entry point an examiner (or you, six months from now) will look for first.
#
# Windows note: these targets assume Git Bash or WSL. On plain PowerShell run the
# underlying commands from README.md instead.

SHELL := /bin/sh

# Pick the venv interpreter for the platform. .venv/Scripts on Windows, .venv/bin elsewhere.
ifeq ($(OS),Windows_NT)
	PY := backend/.venv/Scripts/python.exe
else
	PY := backend/.venv/bin/python
endif

.PHONY: help install install-backend install-frontend env dev backend frontend \
        data train seed test test-backend test-frontend lint format build \
        docker-up docker-down docker-logs clean fresh

help:
	@echo "CyberSathi targets:"
	@echo "  make install        Install backend (venv) and frontend (npm) dependencies"
	@echo "  make env            Create backend/.env from backend/.env.example if missing"
	@echo "  make dev            Start the API and the web app together"
	@echo "  make backend        Start the FastAPI server only (127.0.0.1:8000)"
	@echo "  make frontend       Start the Vite dev server only (localhost:5173)"
	@echo "  make data           Regenerate the synthetic training datasets"
	@echo "  make train          Train both ML models"
	@echo "  make seed           Seed the knowledge base, quiz bank and demo cohort"
	@echo "  make fresh          data + train + seed --reset  (full rebuild)"
	@echo "  make test           Run every test suite"
	@echo "  make lint           Lint the backend (ruff) and typecheck the frontend"
	@echo "  make build          Production build of the frontend"
	@echo "  make docker-up      docker compose up --build  (web app on :8080)"
	@echo "  make docker-down    Stop the containers"
	@echo "  make clean          Remove caches and build output"
	@echo ""
	@echo "First run:  make install && make fresh && make dev"

install: install-backend install-frontend env

install-backend:
	cd backend && python -m venv .venv
	cd backend && $(abspath $(PY)) -m pip install --upgrade pip
	cd backend && $(abspath $(PY)) -m pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

# The app runs with zero configuration, but SECRET_KEY should be changed for anything shared.
env:
	@if [ ! -f backend/.env ]; then cp backend/.env.example backend/.env && echo "created backend/.env"; else echo "backend/.env already exists"; fi

dev:
	@echo "Starting backend on :8000 and frontend on :5173"
	@echo "Press Ctrl+C to stop both."
	@$(MAKE) -j2 backend frontend

backend:
	cd backend && $(abspath $(PY)) -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

frontend:
	cd frontend && npm run dev

data:
	cd backend && $(abspath $(PY)) ml_training/generate_datasets.py

train:
	cd backend && $(abspath $(PY)) ml_training/train_text_model.py
	cd backend && $(abspath $(PY)) ml_training/train_url_model.py

seed:
	cd backend && $(abspath $(PY)) -m app.seed.run --all

# Full rebuild: new datasets, retrained models, and a reseeded database.
fresh: data train
	cd backend && $(abspath $(PY)) -m app.seed.run --all --reset

test: test-backend test-frontend

test-backend:
	cd backend && $(abspath $(PY)) -m pytest tests/ -q

test-frontend:
	cd frontend && npm test

lint:
	cd backend && $(abspath $(PY)) -m ruff check app ml_training tests
	cd frontend && npx tsc --noEmit -p tsconfig.json
	cd frontend && npm run lint

format:
	cd backend && $(abspath $(PY)) -m ruff format app ml_training tests

build:
	cd frontend && npm run build

docker-up:
	docker compose up --build

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

clean:
	rm -rf frontend/dist backend/.pytest_cache backend/.ruff_cache
	find backend -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
