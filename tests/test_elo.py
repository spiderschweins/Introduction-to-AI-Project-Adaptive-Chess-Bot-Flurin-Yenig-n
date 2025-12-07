"""
Unit tests for ELO estimation and adaptive depth functions.
"""
import pytest
from src.api import _estimate_elo, _adaptive_depth


class TestEloEstimation:
    """Tests for the ELO estimation function."""

    def test_low_acpl_high_elo(self):
        """Low ACPL should result in high ELO."""
        elo = _estimate_elo(25)
        assert 2500 <= elo <= 2800, f"ACPL 25 should give ELO 2500-2800, got {elo}"

    def test_medium_acpl_medium_elo(self):
        """Medium ACPL should result in medium ELO."""
        elo = _estimate_elo(75)
        assert 1400 <= elo <= 1800, f"ACPL 75 should give ELO 1400-1800, got {elo}"

    def test_high_acpl_low_elo(self):
        """High ACPL should result in low ELO."""
        elo = _estimate_elo(150)
        assert 400 <= elo <= 1000, f"ACPL 150 should give ELO 400-1000, got {elo}"

    def test_zero_acpl_max_elo(self):
        """Zero ACPL (perfect play) should give maximum ELO."""
        elo = _estimate_elo(0)
        assert elo == 2800, f"ACPL 0 should give ELO 2800, got {elo}"

    def test_negative_acpl_max_elo(self):
        """Negative ACPL should be handled gracefully."""
        elo = _estimate_elo(-10)
        assert elo == 2800, f"Negative ACPL should give ELO 2800, got {elo}"

    def test_very_high_acpl_min_elo(self):
        """Very high ACPL should be clamped to minimum ELO."""
        elo = _estimate_elo(500)
        assert elo == 400, f"ACPL 500 should give minimum ELO 400, got {elo}"

    def test_elo_decreases_with_acpl(self):
        """ELO should decrease as ACPL increases."""
        elo_low = _estimate_elo(30)
        elo_mid = _estimate_elo(60)
        elo_high = _estimate_elo(120)
        assert elo_low > elo_mid > elo_high, "ELO should decrease as ACPL increases"

    @pytest.mark.parametrize("acpl,min_elo,max_elo", [
        (50, 2000, 2800),
        (100, 1000, 1800),
        (200, 400, 1000),
    ])
    def test_elo_ranges(self, acpl, min_elo, max_elo):
        """Test ELO estimation for various ACPL values."""
        elo = _estimate_elo(acpl)
        assert min_elo <= elo <= max_elo, f"ACPL {acpl}: expected ELO {min_elo}-{max_elo}, got {elo}"


class TestAdaptiveDepth:
    """Tests for the adaptive depth function."""

    def test_low_elo_low_depth(self):
        """Low ELO should result in low bot depth."""
        depth = _adaptive_depth(1500)
        assert depth == 1, f"ELO 1500 should give depth 1, got {depth}"

    def test_medium_elo_medium_depth(self):
        """Medium ELO should result in medium bot depth."""
        depth = _adaptive_depth(2300)
        assert depth == 3, f"ELO 2300 should give depth 3, got {depth}"

    def test_high_elo_high_depth(self):
        """High ELO should result in high bot depth."""
        depth = _adaptive_depth(2900)
        assert depth == 8, f"ELO 2900 should give depth 8, got {depth}"

    @pytest.mark.parametrize("elo,expected_depth", [
        (1000, 1),
        (1999, 1),
        (2000, 2),  # >= 2000 gets depth 2
        (2100, 2),
        (2199, 2),
        (2200, 3),  # >= 2200 gets depth 3
        (2349, 3),
        (2350, 4),  # >= 2350 gets depth 4
        (2499, 4),
        (2500, 5),  # >= 2500 gets depth 5
        (2649, 5),
        (2650, 6),  # >= 2650 gets depth 6
        (2749, 6),
        (2750, 7),  # >= 2750 gets depth 7
        (2899, 7),
        (2900, 8),  # >= 2900 gets depth 8
        (3000, 8),
    ])
    def test_depth_boundaries(self, elo, expected_depth):
        """Test depth at ELO boundaries."""
        depth = _adaptive_depth(elo)
        assert depth == expected_depth, f"ELO {elo}: expected depth {expected_depth}, got {depth}"

    def test_depth_increases_with_elo(self):
        """Depth should generally increase with ELO."""
        depths = [_adaptive_depth(elo) for elo in [1500, 2100, 2300, 2600, 2900]]
        assert depths == sorted(depths), "Depth should increase with ELO"
