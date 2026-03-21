.PHONY: install seed pipeline test lint format qa app clean

install:
	python -m pip install --upgrade pip
	python -m pip install -e ".[dev]"

seed:
	python -m src.main seed --matches 500 --seed 42

pipeline:
	python -m src.main pipeline

test:
	python -m pytest

lint:
	python -m ruff check src tests app
	python -m black --check src tests app

format:
	python -m black src tests app
	python -m ruff check src tests app --fix

qa: lint test

app:
	python -m streamlit run app/Home.py

clean:
	python -m src.main clean
