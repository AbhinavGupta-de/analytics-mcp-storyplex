# Storyplex Analytics - Makefile
# DevOps CI/CD Local Development Commands

.PHONY: help venv install install-dev lint lint-fix test test-cov security-scan sast sca build docker-build docker-run docker-test docker-push clean all

# Default target
help:
	@echo "Storyplex Analytics - Available Commands"
	@echo "========================================"
	@echo ""
	@echo "Setup:"
	@echo "  make venv           Create virtual environment"
	@echo "  make install        Install production dependencies"
	@echo "  make install-dev    Install development dependencies"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint           Run linting (ruff)"
	@echo "  make lint-fix       Run linting with auto-fix"
	@echo "  make format         Format code with ruff"
	@echo ""
	@echo "Testing:"
	@echo "  make test           Run unit tests"
	@echo "  make test-cov       Run tests with coverage"
	@echo ""
	@echo "Security:"
	@echo "  make security-scan  Run all security scans (SAST + SCA)"
	@echo "  make sast           Run SAST (bandit)"
	@echo "  make sca            Run SCA (pip-audit)"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build   Build Docker image"
	@echo "  make docker-run     Run Docker container"
	@echo "  make docker-test    Test Docker container"
	@echo "  make docker-push    Push to DockerHub"
	@echo "  make docker-scan    Scan Docker image with Trivy"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean          Clean build artifacts"
	@echo "  make all            Run full CI pipeline locally"

# Variables
PYTHON := python3
IMAGE_NAME := storyplex-analytics
IMAGE_TAG := latest
DOCKERHUB_USER ?= $(shell echo $$DOCKERHUB_USERNAME)

# =============================================================================
# Setup
# =============================================================================

venv:
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv .venv
	@echo ""
	@echo "Virtual environment created! Activate it with:"
	@echo "  source .venv/bin/activate"

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install .

install-dev:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"

# =============================================================================
# Code Quality & Linting
# =============================================================================

lint:
	@echo "Running Ruff linter..."
	$(PYTHON) -m ruff check src/ tests/

lint-fix:
	@echo "Running Ruff linter with auto-fix..."
	$(PYTHON) -m ruff check --fix src/ tests/

format:
	@echo "Formatting code with Ruff..."
	$(PYTHON) -m ruff format src/ tests/

# =============================================================================
# Testing
# =============================================================================

test:
	@echo "Running unit tests..."
	$(PYTHON) -m pytest tests/ -v

test-cov:
	@echo "Running tests with coverage..."
	$(PYTHON) -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=xml

# =============================================================================
# Security Scanning
# =============================================================================

security-scan: sast sca
	@echo "All security scans completed."

sast:
	@echo "Running SAST (Static Application Security Testing) with Bandit..."
	$(PYTHON) -m bandit -r src/ -f json -o bandit-report.json || true
	$(PYTHON) -m bandit -r src/ -ll

sca:
	@echo "Running SCA (Software Composition Analysis) with pip-audit..."
	$(PYTHON) -m pip_audit --format json --output pip-audit-report.json || true
	$(PYTHON) -m pip_audit

# =============================================================================
# Docker
# =============================================================================

docker-build:
	@echo "Building Docker image..."
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .

docker-run:
	@echo "Running Docker container..."
	docker run --rm -it $(IMAGE_NAME):$(IMAGE_TAG) bash

docker-test:
	@echo "Testing Docker container (smoke test)..."
	docker run --rm $(IMAGE_NAME):$(IMAGE_TAG) python -c "import src; print('Container test passed!')"

docker-scan:
	@echo "Scanning Docker image with Trivy..."
	trivy image --severity HIGH,CRITICAL $(IMAGE_NAME):$(IMAGE_TAG)

docker-push:
	@echo "Pushing Docker image to DockerHub..."
ifndef DOCKERHUB_USER
	$(error DOCKERHUB_USERNAME is not set. Please set it before pushing.)
endif
	docker tag $(IMAGE_NAME):$(IMAGE_TAG) $(DOCKERHUB_USER)/$(IMAGE_NAME):$(IMAGE_TAG)
	docker push $(DOCKERHUB_USER)/$(IMAGE_NAME):$(IMAGE_TAG)

# =============================================================================
# Docker Compose
# =============================================================================

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

# =============================================================================
# Utilities
# =============================================================================

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf bandit-report.json
	rm -rf pip-audit-report.json
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# =============================================================================
# Full CI Pipeline (Local)
# =============================================================================

all: lint test security-scan docker-build docker-test
	@echo ""
	@echo "============================================"
	@echo "Full CI pipeline completed successfully!"
	@echo "============================================"
