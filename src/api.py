from __future__ import annotations
from pathlib import Path
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import chess
import chess.engine

MAX_DEPTH = 8
MODULE_DIR = Path(__file__).resolve().parent

# Support both local Windows binary and Docker Linux binary via env var


def _stockfish_path() -> str:
    env_path = os.getenv("STOCKFISH_PATH")
    if env_path and Path(env_path).is_file():
        return env_path
    # Fallback to local Windows binary
    local_bin = MODULE_DIR / "stockfish-windows-x86-64-avx2.exe"
    if local_bin.is_file():
        return str(local_bin)
    raise RuntimeError("Stockfish binary not found. Set STOCKFISH_PATH or place binary next to api.py")


# Verify Stockfish exists on startup
_stockfish_path()

# ELO estimation from ACPL using power law (derived from empirical data)


def _estimate_elo(acpl: float) -> int:
    """
    Estimates Chess Elo based on Average Centipawn Loss (ACPL).
    Clamped between 400 and 2800.
    """
    if acpl <= 0:
        return 2800  # Handle perfect play or zero error

    # Power law formula derived from the graph
    elo = 323422 * (acpl**-1.2305)

    # Clamp results
    if elo > 2800:
        return 2800
    elif elo < 400:
        return 400

    return int(elo)


# Adaptive depth based on estimated ELO


def _adaptive_depth(elo: int) -> int:
    """
    Returns Stockfish depth based on player's estimated ELO.
    Lower ELO = easier bot (lower depth).
    """
    if elo < 2000:
        return 1  # Expert/CM level
    elif elo < 2200:
        return 2  # National Master
    elif elo < 2350:
        return 3  # International Master
    elif elo < 2500:
        return 4  # Grandmaster
    elif elo < 2650:
        return 5  # Super GM
    elif elo < 2750:
        return 6  # World Champion
    elif elo < 2900:
        return 7  # Superhuman
    else:
        return 8  # Engine level


app = FastAPI(title="Lean Chess", version="0.1")

sessions: dict[str, dict] = {}


class SessionRequest(BaseModel):
    session_id: str
    depth: int = Field(4, ge=1, le=MAX_DEPTH)


class MoveRequest(BaseModel):
    move: str


def _sess(session_id: str) -> dict:
    sess = sessions.get(session_id)
    if not sess:
        sess = sessions[session_id] = {
            "board": chess.Board(),
            "engine": chess.engine.SimpleEngine.popen_uci(_stockfish_path()),
            "depth": 4,
            "moves": [],
            "strength": (1200, "Initial"),
            "total_loss": 0,
            "num_moves": 0,
            "cpl_losses": [],  # Individual CPL per move (for bar chart)
            "avg_losses": [],  # Running ACPL after each move (for sidebar)
        }
    return sess


def _state(sess: dict) -> dict:
    board = sess["board"]
    status = (
        f"Game over ({board.result()})"
        if board.is_game_over()
        else ("White" if board.turn else "Black") + (" to move (check)" if board.is_check() else " to move")
    )
    return {
        "fen": board.fen(),
        "turn": "white" if board.turn else "black",
        "status": status,
        "depth": sess["depth"],
        "moves": sess["moves"],
        "strength": sess["strength"],
        "cpl_losses": sess["cpl_losses"],  # Individual CPL per move (for bar chart)
        "avg_losses": sess["avg_losses"],  # Running ACPL (for sidebar)
    }


def _strength(sess: dict, move: chess.Move) -> tuple[int, str]:
    board = sess["board"]
    engine = sess["engine"]

    # Step 1: Find the best move and evaluate after it
    result = engine.play(board, chess.engine.Limit(depth=8))
    best_move = result.move
    board.push(best_move)
    best_eval = engine.analyse(board, chess.engine.Limit(depth=8))["score"].relative.score(mate_score=10000)
    board.pop()

    # Step 2: Evaluate after the played move
    board.push(move)
    played_eval = engine.analyse(board, chess.engine.Limit(depth=8))["score"].relative.score(mate_score=10000)
    board.pop()

    # Step 3: Compute CPL (played_eval - best_eval, as per perspective adjustment)
    # This gives positive loss if played move is worse
    cpl = played_eval - best_eval
    loss = max(0, cpl)  # Clamp to 0 for negative CPL (better moves)

    # Store individual CPL for this move
    sess["cpl_losses"].append(loss)

    # Update cumulative stats for running average (ACPL)
    sess["total_loss"] += loss
    sess["num_moves"] += 1
    avg_loss = sess["total_loss"] / sess["num_moves"]
    sess["avg_losses"].append(avg_loss)

    # Use power-law formula for ELO estimation
    elo = _estimate_elo(avg_loss)

    # Adapt bot depth to player's estimated ELO
    sess["depth"] = _adaptive_depth(elo)

    summary = f"ACPL: {avg_loss:.1f}, Bot depth: {sess['depth']}"

    return elo, summary


def _apply_move(sess: dict, move: chess.Move) -> str:
    board = sess["board"]
    san = board.san(move)
    board.push(move)
    sess["moves"].append(san)
    return san


@app.post("/session")
def new_session(req: SessionRequest):
    sess = _sess(req.session_id)
    sess["depth"] = req.depth
    sess["board"] = chess.Board()
    sess["moves"] = []
    sess["strength"] = (1200, "Initial")
    sess["total_loss"] = 0
    sess["num_moves"] = 0
    sess["cpl_losses"] = []  # Reset individual CPL
    sess["avg_losses"] = []  # Reset running ACPL
    return _state(sess)


@app.get("/session/{session_id}")
def get_session(session_id: str):
    sess = _sess(session_id)
    return _state(sess)


@app.post("/session/{session_id}/move")
def player_move(session_id: str, req: MoveRequest):
    sess = _sess(session_id)
    board = sess["board"]
    try:
        move = board.parse_uci(req.move)
        if move not in board.legal_moves:
            raise ValueError("Illegal move")
        sess["strength"] = _strength(sess, move)
        _apply_move(sess, move)
        return _state(sess)
    except Exception as exc:
        raise HTTPException(400, f"Invalid move: {exc}") from exc


@app.post("/session/{session_id}/bot")
def bot_move(session_id: str):
    sess = _sess(session_id)
    board = sess["board"]
    if board.is_game_over():
        raise HTTPException(400, "Game over")
    if board.turn == chess.WHITE:
        raise HTTPException(400, "It's your turn to move")
    try:
        result = sess["engine"].play(board, chess.engine.Limit(depth=sess["depth"]))
        san = board.san(result.move)
        board.push(result.move)
        sess["moves"].append(san)
        return _state(sess)
    except Exception as exc:
        raise HTTPException(503, f"Stockfish failed: {exc}") from exc


@app.delete("/session/{session_id}")
def delete_session(session_id: str):
    if session_id in sessions:
        sessions[session_id]["engine"].quit()
        del sessions[session_id]
    return {"message": "Session deleted"}


def main():
    """
    Entry point for running the API server from command line.
    Supports command-line arguments for configuration.
    """
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(
        description="Adaptive Chess Bot API Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.api                     # Run with defaults (localhost:8000)
  python -m src.api --port 8080         # Run on port 8080
  python -m src.api --host 0.0.0.0      # Listen on all interfaces
  python -m src.api --reload            # Enable auto-reload for development
        """,
    )

    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind the server to (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes (default: 1)")

    args = parser.parse_args()

    print(f"Starting Adaptive Chess Bot API on {args.host}:{args.port}")
    print(f"Stockfish path: {_stockfish_path()}")
    print(f"API docs available at: http://{args.host}:{args.port}/docs")

    uvicorn.run(
        "src.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
    )


if __name__ == "__main__":
    main()
