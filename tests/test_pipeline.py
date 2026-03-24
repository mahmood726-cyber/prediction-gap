"""Tests for Prediction Gap pipeline."""
import sys, math, numpy as np, pytest
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent))
from src.pipeline import compute_prediction_interval, classify_discordance


class TestPI:
    def test_homogeneous_pi_equals_ci(self):
        """With tau2=0, PI should be close to CI (only t vs z difference)."""
        yi = np.array([-0.5, -0.5, -0.5, -0.5, -0.5])
        sei = np.array([0.1, 0.1, 0.1, 0.1, 0.1])
        r = compute_prediction_interval(yi, sei)
        ratio = r['pi_ci_ratio']
        assert 0.9 < ratio < 2.0, f"PI/CI ratio {ratio} too large for homogeneous data"

    def test_heterogeneous_pi_wider(self):
        """With heterogeneity, PI should be much wider than CI."""
        yi = np.array([-1.5, -0.5, 0.0, 0.5, 1.0])
        sei = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
        r = compute_prediction_interval(yi, sei)
        assert r['pi_ci_ratio'] > 2.0, f"PI/CI ratio {r['pi_ci_ratio']} too small for heterogeneous"

    def test_pi_contains_ci(self):
        """PI should always be at least as wide as CI."""
        yi = np.array([-0.8, -0.6, -0.4, -0.2, 0.0])
        sei = np.array([0.15, 0.2, 0.25, 0.3, 0.35])
        r = compute_prediction_interval(yi, sei)
        assert r['pi_lo'] <= r['ci_lo']
        assert r['pi_hi'] >= r['ci_hi']

    def test_k3_works(self):
        r = compute_prediction_interval(np.array([-0.5, -0.3, -0.1]), np.array([0.2, 0.2, 0.2]))
        assert r is not None
        assert math.isfinite(r['pi_lo'])

    def test_k2_returns_none(self):
        r = compute_prediction_interval(np.array([-0.5, -0.3]), np.array([0.2, 0.2]))
        assert r is None


class TestClassify:
    def test_false_reassurance(self):
        r = {'ci_lo': -0.5, 'ci_hi': -0.1, 'pi_lo': -0.8, 'pi_hi': 0.3, 'p_value': 0.01}
        assert classify_discordance(r, 'ratio') == 'FALSE_REASSURANCE'

    def test_concordant_sig(self):
        r = {'ci_lo': -0.5, 'ci_hi': -0.1, 'pi_lo': -0.9, 'pi_hi': -0.01, 'p_value': 0.001}
        assert classify_discordance(r, 'ratio') == 'CONCORDANT_SIG'

    def test_concordant_ns(self):
        r = {'ci_lo': -0.3, 'ci_hi': 0.1, 'pi_lo': -0.5, 'pi_hi': 0.5, 'p_value': 0.3}
        assert classify_discordance(r, 'ratio') == 'CONCORDANT_NS'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
