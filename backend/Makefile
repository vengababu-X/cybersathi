# CyberSathi backend
# Windows note: these targets assume Git Bash or WSL. For PowerShell, run the
# underlying commands shown in the README instead.

PY := .venv/Scripts/python.exe
ifeq ($(OS),)
	PY := .venv/bin/python
endif

.PHONY: help install data train seed demo run test lint clean fresh

help:
	@echo "CyberSathi backend targets:"
	@echo "  make install   Create the virtualenv and install dependencies"
	@echo "  make data      Regenerate the training datasets"
	@echo "  make train     Train both ML models (needs 'make data' first)"
	@echo "  make seed      Seed knowledge base, quiz bank and demo cohort"
	@echo "  make run       Start the API on http://127.0.0.1:8000"
	@echo "  make test      Run the test suite"
	@echo "  make fresh     data + train + seed --reset  (full rebuild)"
	@echo "  make demo      Everything, then start the server"

install:
	python -m venv .venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements.txt

data:
	$(PY) ml_training/generate_datasets.py

train:
	$(PY) ml_training/train_text_model.py
	$(PY) ml_training/train_url_model.py

evaluate:
	$(PY) ml_training/evaluate.py

seed:
	$(PY) -m app.seed.run --all

reseed:
	$(PY) -m app.seed.run --all --reset

run:
	$(PY) -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

test:
	$(PY) -m pytest tests/ -v

lint:
	$(PY) -m ruff check app ml_training tests

format:
	$(PY) -m ruff format app ml_training tests

fresh: data train reseed
	@echo "Rebuilt datasets, models and database."

demo: fresh run

clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
