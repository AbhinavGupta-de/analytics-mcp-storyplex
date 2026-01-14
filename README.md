# Storyplex Analytics

Multi-platform fanfiction and web novel analytics scraper with a production-grade CI/CD pipeline.

## Project Overview

Storyplex Analytics is a Python-based application that scrapes and analyzes fanfiction data from platforms like AO3. It features:

- **FastAPI Backend** - RESTful API for analytics and data access
- **React Frontend** - Dashboard for visualizing analytics
- **PostgreSQL Database** - Persistent data storage
- **MCP Server** - Model Context Protocol integration for AI assistants

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Make (optional, for convenience commands)

### Local Development

```bash
# Clone the repository
git clone <repository-url>
cd storyplex-analytics

# Install dependencies
make install-dev

# Run with Docker Compose
make up

# Or run locally
cp .env.example .env
# Edit .env with your configuration
uvicorn src.api.app:app --reload
```

### Available Make Commands

```bash
make help          # Show all available commands
make install-dev   # Install development dependencies
make lint          # Run linting (Ruff)
make test          # Run unit tests
make security-scan # Run SAST + SCA security scans
make docker-build  # Build Docker image
make docker-test   # Test Docker container
make all           # Run full CI pipeline locally
```

## CI/CD Pipeline

This project implements a production-grade CI/CD pipeline using GitHub Actions with DevSecOps principles.

### Pipeline Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Checkout  │────▶│Setup Runtime│────▶│   Linting   │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
       ┌───────────────────────────────────────┼───────────────────────────────────────┐
       │                                       │                                       │
       ▼                                       ▼                                       ▼
┌─────────────┐                         ┌─────────────┐                         ┌─────────────┐
│    SAST     │                         │     SCA     │                         │ Unit Tests  │
│  (Bandit)   │                         │ (pip-audit) │                         │  (pytest)   │
└─────────────┘                         └─────────────┘                         └─────────────┘
       │                                       │                                       │
       └───────────────────────────────────────┼───────────────────────────────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │    Build    │
                                        │  (Python)   │
                                        └─────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │Docker Build │
                                        └─────────────┘
                                               │
                        ┌──────────────────────┼──────────────────────┐
                        │                      │                      │
                        ▼                      ▼                      ▼
                 ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
                 │ Image Scan  │        │Runtime Test │        │   CodeQL    │
                 │  (Trivy)    │        │(Smoke Test) │        │  Analysis   │
                 └─────────────┘        └─────────────┘        └─────────────┘
                        │                      │                      │
                        └──────────────────────┼──────────────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │ Docker Push │
                                        │ (DockerHub) │
                                        └─────────────┘
```

### CI/CD Stages Explained

| Stage | Tool | Purpose | Why It Matters |
|-------|------|---------|----------------|
| **Lint** | Ruff | Enforce coding standards | Prevents technical debt and maintains code consistency |
| **SAST** | Bandit + CodeQL | Static security analysis | Detects OWASP Top 10 vulnerabilities in code |
| **SCA** | pip-audit | Dependency vulnerability scan | Identifies supply-chain risks in dependencies |
| **Unit Tests** | pytest | Validate business logic | Prevents regressions and ensures correctness |
| **Build** | Python build | Package application | Validates project configuration |
| **Docker Build** | Docker | Create container image | Ensures consistent deployments |
| **Image Scan** | Trivy | Container vulnerability scan | Prevents vulnerable images from shipping |
| **Runtime Test** | Docker | Smoke test container | Validates container is runnable |
| **Docker Push** | DockerHub | Publish trusted image | Enables downstream CD |

### Security Integration (DevSecOps)

This pipeline implements **shift-left security** - finding vulnerabilities early in development:

1. **SAST (Static Application Security Testing)**
   - Bandit scans Python code for security issues
   - CodeQL performs deep semantic analysis
   - Results surfaced in GitHub Security tab

2. **SCA (Software Composition Analysis)**
   - pip-audit checks dependencies against known CVEs
   - Identifies vulnerable third-party libraries

3. **Container Scanning**
   - Trivy scans Docker images for OS and library vulnerabilities
   - Blocks deployment of images with CRITICAL/HIGH vulnerabilities

## GitHub Secrets Configuration

Configure the following secrets in your GitHub repository settings:

| Secret Name | Purpose | How to Get |
|-------------|---------|------------|
| `DOCKERHUB_USERNAME` | Docker registry username | Your DockerHub username |
| `DOCKERHUB_TOKEN` | Secure registry access | Generate at [DockerHub Security Settings](https://hub.docker.com/settings/security) |

### Setting Up Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with its corresponding value

> ⚠️ **Important**: Never hardcode secrets in your code or commit them to the repository.

## Running the CI Pipeline Locally

You can simulate the CI pipeline locally using Make:

```bash
# Run full pipeline
make all

# Or run individual stages
make lint           # Code quality
make test           # Unit tests
make sast           # Security scan (SAST)
make sca            # Dependency scan (SCA)
make docker-build   # Build image
make docker-scan    # Scan image (requires Trivy)
make docker-test    # Smoke test
```

## Project Structure

```
storyplex-analytics/
├── .github/
│   └── workflows/
│       └── ci.yml          # CI/CD pipeline definition
├── src/
│   ├── api/                # FastAPI application
│   ├── db/                 # Database models & connection
│   ├── scrapers/           # Web scrapers
│   └── mcp_server.py       # MCP server implementation
├── tests/                  # Unit tests
├── frontend/               # React frontend
├── Dockerfile              # Container image definition
├── docker-compose.yml      # Local development setup
├── Makefile                # Development commands
├── pyproject.toml          # Python project configuration
├── bandit.yaml             # SAST configuration
└── README.md               # This file
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/storyplex
ANTHROPIC_API_KEY=your-api-key  # For LLM features
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Ensure all CI checks pass (`make all`)
4. Submit a pull request
