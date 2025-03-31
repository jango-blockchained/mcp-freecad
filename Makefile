.PHONY: help setup test run clean format

help:
	@echo "Available commands:"
	@echo "  make setup    - Set up the development environment"
	@echo "  make test     - Run tests"
	@echo "  make run      - Start the server"
	@echo "  make clean    - Clean up generated files"
	@echo "  make format   - Format code with black and isort"

setup:
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt

test:
	. venv/bin/activate && python -m pytest

run:
	. venv/bin/activate && PYTHONPATH=. python app.py

clean:
	rm -rf __pycache__
	rm -rf src/**/__pycache__
	rm -rf tests/__pycache__
	rm -rf .pytest_cache
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

format:
	. venv/bin/activate && pip install black isort
	. venv/bin/activate && black src tests app.py
	. venv/bin/activate && isort src tests app.py 