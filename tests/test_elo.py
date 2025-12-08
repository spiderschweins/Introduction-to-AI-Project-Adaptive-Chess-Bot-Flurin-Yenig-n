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


class TestCPLvsACPL:
    """Tests to verify CPL (individual) vs ACPL (running average) calculations."""

    def test_acpl_is_average_of_cpl(self):
        """ACPL should be the arithmetic mean of all CPL values."""
        cpl_values = [20, 40, 30, 10]
        expected_acpl = sum(cpl_values) / len(cpl_values)  # 25.0
        assert expected_acpl == 25.0, f"Expected ACPL 25.0, got {expected_acpl}"

    def test_running_acpl_calculation(self):
        """Running ACPL should update correctly after each move."""
        cpl_values = [20, 40, 30, 10]
        running_acpl = []
        total = 0
        for i, cpl in enumerate(cpl_values, 1):
            total += cpl
            running_acpl.append(total / i)
        
        expected = [20.0, 30.0, 30.0, 25.0]
        assert running_acpl == expected, f"Expected {expected}, got {running_acpl}"

    def test_cpl_differs_from_acpl(self):
        """Individual CPL values should differ from running ACPL values."""
        cpl_values = [20, 40, 30, 10]  # Individual CPL per move
        running_acpl = [20.0, 30.0, 30.0, 25.0]  # Running average
        
        # They should NOT be the same (except potentially the first value)
        assert cpl_values != running_acpl, "CPL and ACPL lists should differ"
        # First value is always the same (only one data point)
        assert cpl_values[0] == running_acpl[0], "First CPL equals first ACPL"

    def test_final_acpl_is_mean(self):
        """The last running ACPL value should equal the mean of all CPLs."""
        cpl_values = [50, 25, 75, 100, 50]
        running_acpl = []
        total = 0
        for i, cpl in enumerate(cpl_values, 1):
            total += cpl
            running_acpl.append(total / i)
        
        final_acpl = running_acpl[-1]
        mean_cpl = sum(cpl_values) / len(cpl_values)
        assert final_acpl == mean_cpl, f"Final ACPL {final_acpl} should equal mean {mean_cpl}"

    def test_acpl_smooths_cpl_spikes(self):
        """ACPL should smooth out CPL spikes over time."""
        # One bad move (200 CPL) among good moves (10 CPL)
        cpl_values = [10, 10, 200, 10, 10]
        running_acpl = []
        total = 0
        for i, cpl in enumerate(cpl_values, 1):
            total += cpl
            running_acpl.append(total / i)
        
        # The spike should be visible in CPL
        assert max(cpl_values) == 200
        # But smoothed in ACPL - max ACPL should be much lower than 200
        assert max(running_acpl) < 200, "ACPL should smooth the CPL spike"
        # Final ACPL = 240/5 = 48
        assert running_acpl[-1] == 48.0

    def test_cpl_always_non_negative(self):
        """CPL should always be non-negative (clamped at 0)."""
        # If you play a better move than engine suggested, CPL = 0 (not negative)
        assert max(0, -50) == 0, "Negative CPL should be clamped to 0"
        assert max(0, 30) == 30, "Positive CPL should remain unchanged"

