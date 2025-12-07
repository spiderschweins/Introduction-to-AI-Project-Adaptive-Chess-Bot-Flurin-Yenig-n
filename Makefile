# Makefile for Adaptive Chess Bot
# Automates installation, testing, linting, and running

.PHONY: install test lint format run-api run-ui run docker-build docker-run clean help

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install dependencies"
	@echo "  test         - Run pytest tests"
	@echo "  lint         - Run flake8 linter"
	@echo "  format       - Format code with black"
	@echo "  run-api      - Start FastAPI backend"
	@echo "  run-ui       - Start Streamlit frontend"
	@echo "  run          - Start both backend and frontend"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run Docker container"
	@echo "  clean        - Remove cache files"

# Install dependencies
install:
	pip install -r requirements.txt
	pip install -e .
	pip install pytest pytest-cov flake8 black

# Run tests with pytest
test:
	pytest tests/ -v --cov=src --cov-report=term-missing

# Run linter
lint:
	flake8 src/ tests/ --max-line-length=120 --ignore=E501,W503

# Format code
format:
	black src/ tests/ --line-length=120

# Run FastAPI backend
run-api:
	uvicorn src.api:app --reload --host 0.0.0.0 --port 8000

# Run Streamlit frontend
run-ui:
	streamlit run src/app.py --server.port 8501

# Run both (requires two terminals or background process)
run:
	@echo "Starting backend and frontend..."
	@echo "Run 'make run-api' in one terminal"
	@echo "Run 'make run-ui' in another terminal"
	@echo "Or use: ./run_app.ps1 (Windows) or docker-compose up"

# Docker commands
docker-build:
	docker build -t adaptive-chess-bot .

docker-run:
	docker run -p 8000:8000 -p 8501:8501 adaptive-chess-bot

docker-compose-up:
	docker-compose up --build

# Clean up cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".coverage" -delete 2>/dev/null || true
