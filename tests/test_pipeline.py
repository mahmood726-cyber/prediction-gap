"""Tests for Prediction Gap pipeline."""
import math
import sys
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent))
from src.pipeline import (
    classify_discordance,
    compute_prediction_interval,
    resolve_paths,
    run_pipeline,
)


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


class TestPIEdgeCases:
    def test_large_k_narrow_pi(self):
        """Large k should give narrower PI due to t-dist approaching normal."""
        k = 50
        yi = np.full(k, -0.3)
        sei = np.full(k, 0.1)
        r = compute_prediction_interval(yi, sei)
        # With tau2=0 and large k, PI/CI ratio should be close to 1
        assert r['pi_ci_ratio'] < 1.5

    def test_k3_wide_pi(self):
        """k=3 should give very wide PI due to t(1) distribution."""
        yi = np.array([-0.5, -0.3, -0.1])
        sei = np.array([0.1, 0.1, 0.1])
        r = compute_prediction_interval(yi, sei)
        # t(1) critical value is 12.7, so PI should be much wider
        assert r['pi_ci_ratio'] > 3.0

    def test_equal_studies_zero_tau2(self):
        """Identical studies should give tau2=0."""
        yi = np.array([0.5, 0.5, 0.5, 0.5, 0.5])
        sei = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
        r = compute_prediction_interval(yi, sei)
        assert r['tau2'] == 0.0

    def test_very_heterogeneous(self):
        """Extremely heterogeneous data should give very wide PI."""
        yi = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
        sei = np.array([0.1, 0.1, 0.1, 0.1, 0.1])
        r = compute_prediction_interval(yi, sei)
        assert r['pi_ci_ratio'] > 3.0
        assert r['I2'] > 90

    def test_positive_effects(self):
        """Works with positive effects (risk increase)."""
        yi = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
        sei = np.array([0.15, 0.15, 0.15, 0.15, 0.15])
        r = compute_prediction_interval(yi, sei)
        assert r['theta'] > 0
        assert r['ci_lo'] > 0  # significant

    def test_single_outlier(self):
        """One outlier study inflates tau2 and PI."""
        yi = np.array([-0.5, -0.5, -0.5, -0.5, 2.0])
        sei = np.array([0.1, 0.1, 0.1, 0.1, 0.1])
        r = compute_prediction_interval(yi, sei)
        assert r['tau2'] > 0
        assert r['pi_ci_ratio'] > 3.0


class TestClassifyEdgeCases:
    def test_ci_exactly_at_null(self):
        """CI boundary exactly at 0 should be non-significant."""
        r = {'ci_lo': -0.3, 'ci_hi': 0.0, 'pi_lo': -0.5, 'pi_hi': 0.5, 'p_value': 0.05}
        assert classify_discordance(r, 'ratio') == 'CONCORDANT_NS'

    def test_positive_ci_excludes_null(self):
        """CI entirely above 0 (risk increase)."""
        r = {'ci_lo': 0.1, 'ci_hi': 0.5, 'pi_lo': -0.2, 'pi_hi': 0.8, 'p_value': 0.001}
        assert classify_discordance(r, 'ratio') == 'FALSE_REASSURANCE'

    def test_positive_concordant(self):
        """Both CI and PI above 0."""
        r = {'ci_lo': 0.1, 'ci_hi': 0.5, 'pi_lo': 0.01, 'pi_hi': 0.8, 'p_value': 0.001}
        assert classify_discordance(r, 'ratio') == 'CONCORDANT_SIG'

    def test_difference_scale(self):
        """Works on difference scale too."""
        r = {'ci_lo': -3.0, 'ci_hi': -1.0, 'pi_lo': -5.0, 'pi_hi': 0.5, 'p_value': 0.001}
        assert classify_discordance(r, 'difference') == 'FALSE_REASSURANCE'


class TestPIProperties:
    """Mathematical properties that must always hold."""

    def test_pi_always_contains_ci(self):
        """PI must always be at least as wide as CI (for DL)."""
        rng = np.random.RandomState(42)
        for _ in range(20):
            k = rng.randint(3, 30)
            yi = rng.normal(0, 1, k)
            sei = np.abs(rng.normal(0.2, 0.05, k)) + 0.01
            r = compute_prediction_interval(yi, sei)
            if r is not None:
                assert r['pi_lo'] <= r['ci_lo'] + 1e-10, f"PI lower > CI lower: {r}"
                assert r['pi_hi'] >= r['ci_hi'] - 1e-10, f"PI upper < CI upper: {r}"

    def test_pi_width_increases_with_tau2(self):
        """More heterogeneity -> wider PI."""
        base_yi = np.array([-0.5, -0.3, -0.1, 0.1, 0.3])
        sei = np.array([0.15, 0.15, 0.15, 0.15, 0.15])
        r_homo = compute_prediction_interval(base_yi * 0 - 0.3, sei)  # homogeneous
        r_hetero = compute_prediction_interval(base_yi, sei)  # heterogeneous
        assert r_hetero['pi_width'] > r_homo['pi_width']

    def test_theta_between_ci_bounds(self):
        """Pooled effect must be within CI."""
        rng = np.random.RandomState(99)
        for _ in range(20):
            k = rng.randint(3, 20)
            yi = rng.normal(-0.5, 0.3, k)
            sei = np.abs(rng.normal(0.2, 0.05, k)) + 0.01
            r = compute_prediction_interval(yi, sei)
            if r is not None:
                assert r['ci_lo'] <= r['theta'] <= r['ci_hi']


def test_run_pipeline_uses_repo_relative_sibling_projects(tmp_path, monkeypatch):
    projects_root = tmp_path / 'projects'
    project_root = projects_root / 'PredictionGap'
    project_root.mkdir(parents=True)

    paths = resolve_paths(project_root=project_root, projects_root=projects_root)
    paths['pairwise_dir'].mkdir(parents=True, exist_ok=True)

    synthetic_review = SimpleNamespace(
        review_id='CD000001',
        analysis_name='Synthetic review',
        yi=np.array([-0.5, -0.4, -0.3, -0.2, -0.1]),
        sei=np.array([0.1, 0.1, 0.1, 0.1, 0.1]),
        scale='ratio',
    )
    monkeypatch.setattr('src.pipeline.load_all_reviews', lambda pairwise_dir, min_k=3: [synthetic_review])

    results, summary = run_pipeline(project_root=project_root, projects_root=projects_root)

    assert len(results) == 1
    assert summary['n_reviews'] == 1
    assert (project_root / 'data' / 'output' / 'prediction_gap_results.csv').exists()
    assert (project_root / 'data' / 'output' / 'prediction_gap_summary.json').exists()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
