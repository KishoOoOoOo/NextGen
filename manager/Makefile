.PHONY: help install install-dev run run-server test lint format clean build dist

# Default target
help:
	@echo "NextGen Hub - Advanced Process Management System"
	@echo ""
	@echo "Available commands:"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  run          - Run desktop application"
	@echo "  run-server   - Run web server only"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linting"
	@echo "  format       - Format code"
	@echo "  clean        - Clean build artifacts"
	@echo "  build        - Build package"
	@echo "  dist         - Create distribution"

# Installation
install:
	pip install -r backend/requirements.txt

install-dev:
	pip install -r backend/requirements.txt
	pip install -e .[dev]

# Running
run:
	python desktop_app.py

run-server:
	python -m manager.backend.app

# Testing
test:
	pytest tests/ -v

# Code quality
lint:
	flake8 manager/ tests/
	mypy manager/

format:
	black manager/ tests/
	isort manager/ tests/

# Build
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build: clean
	python setup.py build

dist: clean
	python setup.py sdist bdist_wheel

# Development helpers
setup-dev: install-dev
	@echo "Development environment setup complete!"

check: lint test
	@echo "All checks passed!"

# Windows specific
run-windows:
	start_orchestratorx.bat

# Docker (if needed in future)
docker-build:
	docker build -t nextgen-hub .

docker-run:
	docker run -p 8000:8000 nextgen-hub 