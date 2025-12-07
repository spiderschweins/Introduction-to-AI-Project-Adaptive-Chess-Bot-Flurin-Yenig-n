"""
Tests for Stockfish integration.
Uses a single shared engine instance to avoid slow startup times.
"""
import pytest
from src.api import _stockfish_path
import chess.engine


# Module-level fixture to reuse Stockfish engine
@pytest.fixture(scope="module")
def engine():
    """Create a shared Stockfish engine for all tests."""
    path = _stockfish_path()
    eng = chess.engine.SimpleEngine.popen_uci(path)
    yield eng
    eng.quit()


class TestStockfish:
    """Tests for Stockfish chess engine integration."""

    def test_stockfish_path_exists(self):
        """Test that Stockfish binary path is valid."""
        path = _stockfish_path()
        assert path is not None
        assert len(path) > 0

    def test_stockfish_launches(self, engine):
        """Test that Stockfish engine is running."""
        assert engine is not None

    def test_stockfish_finds_best_move(self, engine):
        """Test that Stockfish can find a best move."""
        board = chess.Board()
        result = engine.play(board, chess.engine.Limit(depth=1))
        
        assert result.move is not None
        assert result.move in board.legal_moves

    def test_stockfish_analyzes_position(self, engine):
        """Test that Stockfish can analyze a position."""
        board = chess.Board()
        info = engine.analyse(board, chess.engine.Limit(depth=1))
        
        assert "score" in info
