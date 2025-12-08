# Adaptive Chess Bot

An adaptive chess application with CLI, API and web-interface that automatically adjusts difficulty based on player skill level. The bot measures your Average Centipawn Loss (ACPL) to estimate your ELO rating and matches its strength accordingly.


## Setup Instructions

### 1. Create Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

### 3. Install Dev Dependencies (Optional)

For linting and formatting:
```bash
pip install pytest pytest-cov flake8 black==24.3.0
```

> **Note:** Use `black==24.3.0` to avoid compatibility issues with Python 3.12.5.


## How to Run

Use the following to launch the application:

```bash
python -m src.cli play
```

This launches an interactive terminal chess game against the adaptive bot.


## How to Launch the Interface

To start both the backend (FastAPI) and the frontend (Streamlit), run:

```bash
make run
```

Or manually:

```bash
# Terminal 1: API
uvicorn src.api:app --reload --port 8000

# Terminal 2: UI
streamlit run src/app.py
```

Access the web interface at: `http://localhost:8501`


## CLI

The application includes a full command-line interface using `argparse`.

### Example Commands

**Play a game in terminal:**
```bash
python -m src.cli play
python -m src.cli play --depth 3
```

**Analyze a position:**
```bash
python -m src.cli analyze --fen "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
python -m src.cli analyze --fen "..." --depth 15 --lines 3
```

**Estimate ELO from ACPL:**
```bash
python -m src.cli estimate-elo --acpl 50
python -m src.cli estimate-elo --acpl 120
```

**Start server/UI:**
```bash
python -m src.cli server --port 8000
python -m src.cli ui --port 8501
```


## API

Implemented using FastAPI. Available endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/session` | Create new game session |
| GET | `/session/{id}` | Get current game state |
| POST | `/session/{id}/move` | Submit player move (UCI format) |
| POST | `/session/{id}/bot` | Trigger bot response |
| DELETE | `/session/{id}` | End session |

The backend is served with uvicorn at `localhost:8000`.
API documentation available at `http://localhost:8000/docs`.


## Frontend (Streamlit UI)

A web interface that allows users to:
- Play chess against the adaptive bot
- View real-time CPL analysis per move
- Track estimated ELO rating
- See performance charts

Streamlit renders the UI at `localhost:8501`.


## Docker

A Dockerfile is provided to containerize the entire project. Build and run with:

```bash
docker build -t adaptive-chess-bot .
docker run -p 8000:8000 -p 8501:8501 adaptive-chess-bot
```

Or use docker-compose:

```bash
docker-compose up --build
```

Make sure ports 8000 and 8501 are available.


## Packaging (setup.py)

This project uses Python packaging conventions:
- `setup.py` defines the installable structure
- Install locally with:

```bash
pip install .
```

Entry points:
- `chessbot` - Main CLI interface
- `chessbot-api` - API server


## Testing & Automation

The project includes automated tests using pytest.

**Run all tests:**
```bash
make test
```

**Format code with Black:**
```bash
make format
```

**Check code quality with Flake8:**
```bash
make lint
```

**Run all steps at once:**
```bash
./autotest.sh
```


## Project Structure

```
├── src/
│   ├── __init__.py          # Package marker
│   ├── api.py               # FastAPI backend + Stockfish integration
│   ├── app.py               # Streamlit frontend + charts
│   └── cli.py               # Command-line interface (argparse)
├── tests/
│   ├── test_api.py          # API endpoint tests
│   ├── test_cli.py          # CLI argument tests
│   ├── test_elo.py          # ELO estimation tests
│   └── test_stockfish.py    # Engine connectivity tests
├── data/                    # Data files and plots
├── docs/                    # Documentation
├── Dockerfile               # Container definition
├── docker-compose.yml       # Multi-container deployment
├── Makefile                 # Build automation
├── autotest.sh              # Automated test script
├── requirements.txt         # Python dependencies
├── setup.py                 # Package installation
└── README.md                # This file
```


## The AI Technique

### Centipawn Loss (CPL)
Measures move quality by comparing your move to the engine's best move:
```
CPL = Eval(Best Move) - Eval(Your Move)
```

### ELO Estimation
Uses a power-law formula derived from empirical data:
```
ELO = 323422 × (ACPL ^ -1.2305)
```

| ACPL | Estimated ELO |
|------|---------------|
| 25   | 2800 (capped) |
| 50   | ~2625         |
| 100  | ~1118         |
| 200  | ~476          |

Note: ELO is clamped between 400 and 2800.

### Adaptive Depth
Bot strength adjusts based on estimated ELO:

| Player ELO | Bot Depth |
|------------|-----------|
| < 2000     | 1         |
| 2000-2199  | 2         |
| 2200-2349  | 3         |
| 2350-2499  | 4         |
| 2500+      | 5-8       |


## Dependencies and Environment Info

Main libraries used:
- `python-chess` - Chess logic and board representation
- `fastapi` - REST API framework
- `uvicorn` - ASGI server
- `streamlit` - Web UI framework
- `pytest` - Testing framework
- `python-dotenv` - Environment configuration

Python version: 3.10+
Virtual environment: pyenv-virtualenv recommended


## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CHESSBOT_API_URL` | Backend API URL | `http://127.0.0.1:8000` |
| `STOCKFISH_PATH` | Path to Stockfish binary | Auto-detected |


## Expected Output

- Interactive chess game with move-by-move CPL feedback
- Real-time ELO estimation based on playing strength
- Adaptive bot difficulty matching player skill
- Performance visualization charts
