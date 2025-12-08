"""
Integration tests for the FastAPI endpoints.
Tests are designed to be fast and avoid long Stockfish computations.
"""
import pytest
from fastapi.testclient import TestClient
from src.api import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def session_id():
    """Provide a unique session ID for testing."""
    import time
    return f"pytest_test_{int(time.time())}"


class TestSessionEndpoints:
    """Tests for session management endpoints."""

    def test_create_session(self, client, session_id):
        """Test creating a new session."""
        response = client.post("/session", json={"session_id": session_id, "depth": 1})
        assert response.status_code == 200
        data = response.json()
        # Session creation returns the game state, status is the game status
        assert "status" in data
        # Cleanup
        client.delete(f"/session/{session_id}")

    def test_get_session(self, client, session_id):
        """Test retrieving session state."""
        # First create the session
        client.post("/session", json={"session_id": session_id, "depth": 1})
        
        # Then get it
        response = client.get(f"/session/{session_id}")
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected fields
        assert "fen" in data
        assert "turn" in data
        assert "status" in data
        assert "moves" in data
        assert "strength" in data
        assert "depth" in data
        assert "cpl_losses" in data  # Individual CPL per move
        assert "avg_losses" in data  # Running ACPL
        # Cleanup
        client.delete(f"/session/{session_id}")

    def test_initial_state(self, client, session_id):
        """Test that initial game state is correct."""
        client.post("/session", json={"session_id": session_id, "depth": 1})
        response = client.get(f"/session/{session_id}")
        data = response.json()
        
        assert data["turn"] == "white"
        assert "move" in data["status"].lower() or "white" in data["status"].lower()  # Game is ongoing
        assert data["moves"] == []
        assert data["avg_losses"] == []
        # Cleanup
        client.delete(f"/session/{session_id}")

    def test_delete_session(self, client, session_id):
        """Test deleting a session."""
        # Create session
        client.post("/session", json={"session_id": session_id, "depth": 1})
        
        # Delete it
        response = client.delete(f"/session/{session_id}")
        assert response.status_code == 200


class TestMoveEndpoints:
    """Tests for move-related endpoints."""

    def test_valid_move(self, client, session_id):
        """Test making a valid move."""
        client.post("/session", json={"session_id": session_id, "depth": 1})
        
        response = client.post(f"/session/{session_id}/move", json={"move": "e2e4"})
        assert response.status_code == 200
        data = response.json()
        assert "e4" in data["moves"] or "e2e4" in str(data["moves"])
        # Cleanup
        client.delete(f"/session/{session_id}")

    def test_invalid_move_format(self, client, session_id):
        """Test that invalid move format is rejected."""
        client.post("/session", json={"session_id": session_id, "depth": 1})
        
        response = client.post(f"/session/{session_id}/move", json={"move": "xyz"})
        assert response.status_code == 400
        # Cleanup
        client.delete(f"/session/{session_id}")

    def test_illegal_move(self, client, session_id):
        """Test that illegal chess moves are rejected."""
        client.post("/session", json={"session_id": session_id, "depth": 1})
        
        # Try to move a piece that can't move there (pawn can't jump 3 squares)
        response = client.post(f"/session/{session_id}/move", json={"move": "e2e5"})
        assert response.status_code == 400
        # Cleanup
        client.delete(f"/session/{session_id}")

    def test_bot_move_on_wrong_turn(self, client, session_id):
        """Test that bot can't move on human's turn."""
        client.post("/session", json={"session_id": session_id, "depth": 1})
        
        # Try bot move on white's turn (should fail)
        response = client.post(f"/session/{session_id}/bot")
        assert response.status_code == 400
        # Cleanup
        client.delete(f"/session/{session_id}")


class TestAPIStructure:
    """Tests for API structure and responses."""

    def test_session_response_structure(self, client, session_id):
        """Test that session response has correct structure."""
        client.post("/session", json={"session_id": session_id, "depth": 1})
        response = client.get(f"/session/{session_id}")
        data = response.json()
        
        # Check all required fields exist (including both cpl_losses and avg_losses)
        required_fields = ["fen", "turn", "status", "moves", "strength", "depth", "cpl_losses", "avg_losses"]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"
        
        # Check types
        assert isinstance(data["fen"], str)
        assert isinstance(data["turn"], str)
        assert isinstance(data["status"], str)
        assert isinstance(data["moves"], list)
        assert isinstance(data["strength"], list)
        assert isinstance(data["depth"], int)
        assert isinstance(data["cpl_losses"], list)  # Individual CPL per move
        assert isinstance(data["avg_losses"], list)  # Running ACPL
        # Cleanup
        client.delete(f"/session/{session_id}")

    def test_strength_tuple_structure(self, client, session_id):
        """Test that strength field is a tuple of [elo, description]."""
        client.post("/session", json={"session_id": session_id, "depth": 1})
        response = client.get(f"/session/{session_id}")
        data = response.json()
        
        assert len(data["strength"]) == 2
        assert isinstance(data["strength"][0], int)  # ELO
        assert isinstance(data["strength"][1], str)  # Description
        # Cleanup
        client.delete(f"/session/{session_id}")
