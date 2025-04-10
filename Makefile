# Set default goal to help
.DEFAULT_GOAL := help

# Define Python interpreter from venv
VENV_PYTHON = .venv/bin/python
ACTIVATE = . .venv/bin/activate

# Define source and test directories
SRC_DIRS = src tests
PYTHON_FILES = $(shell find $(SRC_DIRS) -name '*.py') setup.py app.py

# AppImage settings
APPIMAGE_FILE = FreeCAD.AppImage
EXTRACT_DIR = squashfs-root

.PHONY: help setup lint test check run clean format download-appimage extract-appimage

help:
	@echo "Available commands:"
	@echo "  make setup             - Set up the development environment (venv, install reqs)"
	@echo "  make download-appimage - Download the FreeCAD AppImage"
	@echo "  make extract-appimage  - Extract the FreeCAD AppImage (downloads if needed)"
	@echo "  make lint              - Run linters (flake8)"
	@echo "  make test              - Run tests with pytest"
	@echo "  make check             - Run linters and tests"
	@echo "  make run               - Start the server (app.py)"
	@echo "  make format            - Format code with black and isort"
	@echo "  make clean             - Clean up generated files (venv, pycache, coverage, build, AppImage)"

setup:
	@echo "Creating virtual environment..."
	python3 -m venv .venv
	@echo "Installing requirements..."
	$(ACTIVATE) && $(VENV_PYTHON) -m pip install --upgrade pip
	$(ACTIVATE) && $(VENV_PYTHON) -m pip install -r requirements.txt -r requirements-dev.txt
	@echo "Setup complete. Activate with: source .venv/bin/activate"

# Rule to download the AppImage
$(APPIMAGE_FILE):
	@echo "Downloading FreeCAD AppImage..."
	$(ACTIVATE) && $(VENV_PYTHON) download_appimage.py --output $(APPIMAGE_FILE)

# Rule to extract the AppImage (depends on download)
$(EXTRACT_DIR):
	@echo "Extracting $(APPIMAGE_FILE) to $(EXTRACT_DIR)/..."
	$(ACTIVATE) && $(VENV_PYTHON) extract_appimage.py $(APPIMAGE_FILE)

# User-friendly targets
download-appimage: $(APPIMAGE_FILE)

extract-appimage: $(EXTRACT_DIR)

lint:
	@echo "Running flake8 linter..."
	$(ACTIVATE) && $(VENV_PYTHON) -m flake8 $(PYTHON_FILES)

test:
	@echo "Running tests with pytest..."
	$(ACTIVATE) && $(VENV_PYTHON) -m pytest

check: lint test
	@echo "Checks passed."

run:
	@echo "Starting server..."
	$(ACTIVATE) && PYTHONPATH=. $(VENV_PYTHON) app.py

clean:
	@echo "Cleaning up..."
	rm -rf .venv
	rm -rf $(APPIMAGE_FILE)
	rm -rf $(EXTRACT_DIR)
	rm -rf __pycache__
	rm -rf $(SRC_DIRS)/**/__pycache__
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info
	find . -type f -name '*.pyc' -delete
	find . -type f -name '*~' -delete

format:
	@echo "Formatting code with black and isort..."
	$(ACTIVATE) && $(VENV_PYTHON) -m pip install black isort
	$(ACTIVATE) && $(VENV_PYTHON) -m black $(PYTHON_FILES)
	$(ACTIVATE) && $(VENV_PYTHON) -m isort $(PYTHON_FILES)
