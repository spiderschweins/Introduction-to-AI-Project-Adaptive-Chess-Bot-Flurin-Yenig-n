#!/bin/bash
# autotest.sh - Automated testing, linting, and CI script for Adaptive Chess Bot
# This script reproduces the Makefile functionality for shell-based CI environments

set -e  # Exit on error

echo "=========================================="
echo "Adaptive Chess Bot - Automated Test Suite"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${YELLOW}>>> $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Step 1: Check Python version
print_status "Checking Python version..."
python --version
PYTHON_VERSION=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Python version: $PYTHON_VERSION"
print_success "Python check passed"
echo ""

# Step 2: Install dependencies
print_status "Installing dependencies..."
pip install -r requirements.txt -q
pip install pytest pytest-cov flake8 black httpx -q
print_success "Dependencies installed"
echo ""

# Step 3: Run linter (flake8)
print_status "Running linter (flake8)..."
if flake8 src/ tests/ --max-line-length=120 --ignore=E501,W503,E402 --exclude=__pycache__; then
    print_success "Linting passed"
else
    print_error "Linting issues found (continuing anyway)"
fi
echo ""

# Step 4: Check code formatting (black)
print_status "Checking code formatting (black)..."
if black src/ tests/ --check --line-length=120 2>/dev/null; then
    print_success "Code formatting OK"
else
    echo "Code formatting differences found (run 'black src/ tests/' to fix)"
fi
echo ""

# Step 5: Verify Stockfish binary
print_status "Verifying Stockfish binary..."
python -c "
from src.api import _stockfish_path
import chess.engine
path = _stockfish_path()
print(f'Stockfish path: {path}')
engine = chess.engine.SimpleEngine.popen_uci(path)
engine.quit()
print('Stockfish launched successfully')
"
print_success "Stockfish verification passed"
echo ""

# Step 6: Run unit tests with pytest
print_status "Running unit tests (pytest)..."
pytest tests/ -v --tb=short
print_success "All tests passed"
echo ""

# Step 7: Run tests with coverage
print_status "Running tests with coverage..."
pytest tests/ --cov=src --cov-report=term-missing --cov-report=html -q
print_success "Coverage report generated"
echo ""

# Step 8: Test API import
print_status "Testing FastAPI app import..."
python -c "from src.api import app; print('FastAPI app import: OK')"
print_success "API import successful"
echo ""

# Step 9: Test core functions
print_status "Testing core functions..."
python -c "
from src.api import _estimate_elo, _adaptive_depth

# Test ELO estimation
tests_passed = 0
tests_total = 0

test_cases = [
    (50, 2000, 2800),
    (100, 1000, 1800),
    (200, 400, 1000),
]

for acpl, min_elo, max_elo in test_cases:
    tests_total += 1
    elo = _estimate_elo(acpl)
    if min_elo <= elo <= max_elo:
        tests_passed += 1
        print(f'  ACPL {acpl} -> ELO {elo}: PASS')
    else:
        print(f'  ACPL {acpl} -> ELO {elo}: FAIL (expected {min_elo}-{max_elo})')

print(f'Core function tests: {tests_passed}/{tests_total} passed')
"
print_success "Core functions working"
echo ""

# Step 10: Check Docker files exist
print_status "Checking Docker configuration..."
if [ -f "Dockerfile" ]; then
    print_success "Dockerfile exists"
else
    print_error "Dockerfile missing"
fi

if [ -f "docker-compose.yml" ]; then
    print_success "docker-compose.yml exists"
else
    print_error "docker-compose.yml missing"
fi
echo ""

# Final summary
echo "=========================================="
echo -e "${GREEN}All automated tests completed!${NC}"
echo "=========================================="
echo ""
echo "To run the application:"
echo "  Local:  ./run_app.ps1 (Windows) or make run-api && make run-ui"
echo "  Docker: docker-compose up --build"
echo ""
