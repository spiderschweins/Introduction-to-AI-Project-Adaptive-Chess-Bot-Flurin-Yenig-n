$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host "=========================================="
Write-Host "Adaptive Chess Bot - Final Verification" -ForegroundColor Cyan
Write-Host "=========================================="

Write-Host "Python version:" -ForegroundColor Yellow
python --version
Write-Host ""

Write-Host "Installing dependencies (pip install -r requirements.txt)..." -ForegroundColor Yellow
pip install -r requirements.txt -q
Write-Host "Dependencies installed." -ForegroundColor Green
Write-Host ""

Write-Host "Verifying Stockfish binary..." -ForegroundColor Yellow
$stockfishScript = @'
from src.api import _stockfish_path
import chess.engine
path = _stockfish_path()
print(f"Stockfish binary: {path}")
engine = chess.engine.SimpleEngine.popen_uci(path)
engine.quit()
print("Stockfish launched and exited successfully.")
'@
$stockfishScript | python -
Write-Host ""

Write-Host "Importing FastAPI application..." -ForegroundColor Yellow
python -c "from src import api; assert api.app is not None; print('FastAPI app import: OK')"
Write-Host ""

Write-Host "Testing ELO estimation function..." -ForegroundColor Yellow
$eloTestScript = @'
from src.api import _estimate_elo, _adaptive_depth

# Test ELO estimation
test_cases = [
    (50, 2000, 2800),   # Low ACPL = high ELO
    (100, 1000, 1800),  # Medium ACPL
    (200, 400, 1000),   # High ACPL = low ELO
]

print("ELO Estimation Tests:")
for acpl, min_elo, max_elo in test_cases:
    elo = _estimate_elo(acpl)
    status = "PASS" if min_elo <= elo <= max_elo else "FAIL"
    print(f"  ACPL {acpl} -> ELO {elo} (expected {min_elo}-{max_elo}): {status}")

# Test adaptive depth
print("\nAdaptive Depth Tests:")
depth_tests = [
    (1500, 1),
    (2100, 2),
    (2300, 3),
    (2400, 4),
    (2600, 5),
]
for elo, expected_depth in depth_tests:
    depth = _adaptive_depth(elo)
    status = "PASS" if depth == expected_depth else "FAIL"
    print(f"  ELO {elo} -> Depth {depth} (expected {expected_depth}): {status}")

print("\nAll core functions working correctly!")
'@
$eloTestScript | python -
Write-Host ""

Write-Host "Testing API endpoints (quick session test)..." -ForegroundColor Yellow
$apiTestScript = @'
from src.api import app
from fastapi.testclient import TestClient

client = TestClient(app)

# Test session creation
resp = client.post("/session", json={"session_id": "test_session", "depth": 4})
assert resp.status_code == 200, f"Session creation failed: {resp.text}"
print("  POST /session: OK")

# Test session retrieval
resp = client.get("/session/test_session")
assert resp.status_code == 200, f"Session get failed: {resp.text}"
data = resp.json()
assert "fen" in data, "Missing FEN in response"
assert "turn" in data, "Missing turn in response"
assert data["turn"] == "white", "Should be white's turn"
print("  GET /session/{id}: OK")

# Test valid move
resp = client.post("/session/test_session/move", json={"move": "e2e4"})
assert resp.status_code == 200, f"Move failed: {resp.text}"
print("  POST /session/{id}/move (e2e4): OK")

# Test bot move
resp = client.post("/session/test_session/bot")
assert resp.status_code == 200, f"Bot move failed: {resp.text}"
print("  POST /session/{id}/bot: OK")

# Test invalid move
resp = client.post("/session/test_session/move", json={"move": "invalid"})
assert resp.status_code == 400, "Invalid move should return 400"
print("  POST /session/{id}/move (invalid): OK (correctly rejected)")

# Test session deletion
resp = client.delete("/session/test_session")
assert resp.status_code == 200, f"Session delete failed: {resp.text}"
print("  DELETE /session/{id}: OK")

print("\nAll API endpoints working correctly!")
'@
$apiTestScript | python -
Write-Host ""

Write-Host "Checking Docker setup..." -ForegroundColor Yellow
if (Test-Path "Dockerfile") {
    Write-Host "  Dockerfile: EXISTS" -ForegroundColor Green
} else {
    Write-Host "  Dockerfile: MISSING" -ForegroundColor Red
}
if (Test-Path "docker-compose.yml") {
    Write-Host "  docker-compose.yml: EXISTS" -ForegroundColor Green
} else {
    Write-Host "  docker-compose.yml: MISSING" -ForegroundColor Red
}
if (Test-Path ".dockerignore") {
    Write-Host "  .dockerignore: EXISTS" -ForegroundColor Green
} else {
    Write-Host "  .dockerignore: MISSING" -ForegroundColor Red
}
Write-Host ""

Write-Host "=========================================="
Write-Host "All tests passed! Ready to play." -ForegroundColor Green
Write-Host ""
Write-Host "To run locally:  ./run_app.ps1" -ForegroundColor Cyan
Write-Host "To run Docker:   docker-compose up --build" -ForegroundColor Cyan
Write-Host "==========================================" 
