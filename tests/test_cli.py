"""
Tests for the command-line interface (CLI).

Tests cover:
- Argument parsing
- ELO estimation command
- Help text generation
"""

import pytest
import sys
from io import StringIO
from unittest.mock import patch, MagicMock

# Import CLI functions
from src.cli import main, estimate_elo_cmd
from src.api import _estimate_elo, _adaptive_depth


class TestCLIArguments:
    """Test argument parsing for CLI commands."""
    
    def test_help_shows_usage(self):
        """Test that --help shows usage information."""
        with patch.object(sys, 'argv', ['cli', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
    
    def test_no_command_shows_help(self):
        """Test that running without a command shows help."""
        with patch.object(sys, 'argv', ['cli']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
    
    def test_estimate_elo_requires_acpl(self):
        """Test that estimate-elo command requires --acpl argument."""
        with patch.object(sys, 'argv', ['cli', 'estimate-elo']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # argparse exits with code 2 for missing required arguments
            assert exc_info.value.code == 2


class TestEstimateEloCommand:
    """Test the estimate-elo CLI command."""
    
    def test_estimate_elo_valid_input(self, capsys):
        """Test ELO estimation with valid ACPL input."""
        # Create a mock args object
        class MockArgs:
            acpl = 50
        
        estimate_elo_cmd(MockArgs())
        
        captured = capsys.readouterr()
        assert "Input ACPL: 50" in captured.out
        assert "Estimated ELO:" in captured.out
        assert "Recommended Bot Depth:" in captured.out
    
    def test_estimate_elo_low_acpl(self, capsys):
        """Test ELO estimation with low ACPL (strong player)."""
        class MockArgs:
            acpl = 15
        
        estimate_elo_cmd(MockArgs())
        
        captured = capsys.readouterr()
        # Low ACPL should give high ELO
        assert "Input ACPL: 15" in captured.out
    
    def test_estimate_elo_high_acpl(self, capsys):
        """Test ELO estimation with high ACPL (beginner)."""
        class MockArgs:
            acpl = 200
        
        estimate_elo_cmd(MockArgs())
        
        captured = capsys.readouterr()
        assert "Input ACPL: 200" in captured.out


class TestEloCalculations:
    """Test the underlying ELO calculation functions."""
    
    def test_estimate_elo_returns_integer(self):
        """ELO estimation should return an integer."""
        result = _estimate_elo(50)
        assert isinstance(result, int)
    
    def test_estimate_elo_clamped_high(self):
        """Very low ACPL should be clamped to max ELO."""
        result = _estimate_elo(0.1)
        assert result <= 2800
    
    def test_estimate_elo_clamped_low(self):
        """Very high ACPL should be clamped to min ELO."""
        result = _estimate_elo(1000)
        assert result >= 400
    
    def test_estimate_elo_inverse_relationship(self):
        """Lower ACPL should give higher ELO."""
        elo_low_acpl = _estimate_elo(25)
        elo_high_acpl = _estimate_elo(100)
        assert elo_low_acpl > elo_high_acpl
    
    def test_adaptive_depth_returns_valid_range(self):
        """Adaptive depth should always be between 1 and 8."""
        for elo in [400, 1000, 1500, 2000, 2500, 2800]:
            depth = _adaptive_depth(elo)
            assert 1 <= depth <= 8
    
    def test_adaptive_depth_increases_with_elo(self):
        """Higher ELO should result in higher or equal depth."""
        depth_beginner = _adaptive_depth(800)
        depth_expert = _adaptive_depth(2500)
        assert depth_expert >= depth_beginner


class TestCLIIntegration:
    """Integration tests for CLI commands."""
    
    def test_estimate_elo_full_command(self):
        """Test running estimate-elo through the full CLI."""
        with patch.object(sys, 'argv', ['cli', 'estimate-elo', '--acpl', '50']):
            with patch('builtins.print') as mock_print:
                main()
                # Check that something was printed
                assert mock_print.called
    
    def test_analyze_requires_fen(self):
        """Test that analyze command requires --fen argument."""
        with patch.object(sys, 'argv', ['cli', 'analyze']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
