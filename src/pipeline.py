"""The Prediction Gap: CI vs PI discordance across Cochrane meta-analyses.

For each review, computes:
- DL pooled effect + 95% CI
- 95% Prediction interval: theta +/- t_{k-2} * sqrt(tau2 + SE2)
- Discordance: CI excludes null but PI does not

Usage: python -m src.pipeline
"""

import sys
import json
import csv
import time
import math
import os
import numpy as np
from pathlib import Path
from scipy import stats

from src.loader import load_all_reviews

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROJECTS_ROOT = PROJECT_ROOT.parent


def compute_prediction_interval(yi, sei, conf_level=0.95):
    """Compute DL pooled effect, CI, and prediction interval."""
    k = len(yi)
    if k < 3:
        return None

    wi = 1.0 / sei ** 2
    sum_w = np.sum(wi)
    theta_fe = np.sum(wi * yi) / sum_w
    Q = float(np.sum(wi * (yi - theta_fe) ** 2))
    C = float(sum_w - np.sum(wi ** 2) / sum_w)
    tau2 = max(0, (Q - (k - 1)) / C) if C > 0 else 0

    wi_star = 1.0 / (sei ** 2 + tau2)
    theta = float(np.sum(wi_star * yi) / np.sum(wi_star))
    se_theta = float(1.0 / math.sqrt(np.sum(wi_star)))

    alpha = 1 - conf_level

    # 95% Confidence Interval (Wald)
    z_crit = stats.norm.ppf(1 - alpha / 2)
    ci_lo = theta - z_crit * se_theta
    ci_hi = theta + z_crit * se_theta

    # 95% Prediction Interval
    # PI = theta +/- t_{k-2, alpha/2} * sqrt(tau2 + se_theta^2)
    # Accounts for both between-study variance AND estimation uncertainty
    if k > 2:
        t_crit = stats.t.ppf(1 - alpha / 2, k - 2)
        pi_se = math.sqrt(tau2 + se_theta ** 2)
        pi_lo = theta - t_crit * pi_se
        pi_hi = theta + t_crit * pi_se
    else:
        pi_lo = float('-inf')
        pi_hi = float('inf')

    I2 = max(0, (Q - (k - 1)) / Q * 100) if Q > 0 else 0
    p_value = 2 * (1 - stats.norm.cdf(abs(theta / se_theta))) if se_theta > 0 else 1

    return {
        'theta': theta,
        'se': se_theta,
        'tau2': tau2,
        'I2': I2,
        'ci_lo': ci_lo,
        'ci_hi': ci_hi,
        'pi_lo': pi_lo,
        'pi_hi': pi_hi,
        'pi_width': pi_hi - pi_lo,
        'ci_width': ci_hi - ci_lo,
        'pi_ci_ratio': (pi_hi - pi_lo) / (ci_hi - ci_lo) if (ci_hi - ci_lo) > 0 else float('inf'),
        'p_value': p_value,
        'k': k,
    }


def classify_discordance(result, scale):
    """Classify the CI-PI discordance."""
    null = 0.0  # log scale for both ratio and difference

    ci_excludes_null = (result['ci_lo'] > null) or (result['ci_hi'] < null)
    pi_excludes_null = (result['pi_lo'] > null) or (result['pi_hi'] < null)
    p_sig = result['p_value'] < 0.05

    if ci_excludes_null and not pi_excludes_null:
        return 'FALSE_REASSURANCE'  # CI says significant, PI says maybe not
    elif not ci_excludes_null and pi_excludes_null:
        return 'HIDDEN_SIGNAL'  # rare: PI narrower than CI (shouldn't happen)
    elif ci_excludes_null and pi_excludes_null:
        return 'CONCORDANT_SIG'  # both agree: significant
    else:
        return 'CONCORDANT_NS'  # both agree: not significant


def resolve_paths(project_root=None, projects_root=None, pairwise_dir=None, output_dir=None):
    project_root = Path(project_root).resolve() if project_root else PROJECT_ROOT
    projects_root = Path(projects_root).resolve() if projects_root else project_root.parent

    pairwise_candidates = []
    if pairwise_dir:
        pairwise_candidates.append(Path(pairwise_dir).expanduser())
    env_pairwise = os.getenv('PAIRWISE70_DATA_DIR')
    if env_pairwise:
        pairwise_candidates.append(Path(env_pairwise).expanduser())
    pairwise_candidates.extend([
        projects_root / 'Models' / 'Pairwise70' / 'data',
        projects_root / 'Projects' / 'Pairwise70' / 'data',
    ])
    resolved_pairwise = next((path.resolve() for path in pairwise_candidates if path.exists()), pairwise_candidates[0].resolve())

    resolved_output = Path(output_dir).resolve() if output_dir else project_root / 'data' / 'output'
    return {
        'pairwise_dir': resolved_pairwise,
        'output_dir': resolved_output,
    }


def run_pipeline(pairwise_dir=None, output_dir=None, project_root=None, projects_root=None):
    paths = resolve_paths(
        project_root=project_root,
        projects_root=projects_root,
        pairwise_dir=pairwise_dir,
        output_dir=output_dir,
    )
    pairwise_path = paths['pairwise_dir']
    output_path = paths['output_dir']
    output_path.mkdir(parents=True, exist_ok=True)

    print("The Prediction Gap Pipeline")
    print("=" * 35)

    if not pairwise_path.exists():
        print(f"ERROR: Pairwise70 data directory not found: {pairwise_path}")
        return None

    reviews = list(load_all_reviews(pairwise_path, min_k=3))
    if not reviews:
        print(f"ERROR: No eligible reviews found in {pairwise_path}")
        return None
    print(f"  {len(reviews)} reviews loaded")

    results = []
    t0 = time.time()

    for review in reviews:
        r = compute_prediction_interval(review.yi, review.sei)
        if r is None:
            continue

        disc = classify_discordance(r, review.scale)

        row = {
            'review_id': review.review_id,
            'analysis_name': review.analysis_name,
            'k': r['k'],
            'scale': review.scale,
            'theta': round(r['theta'], 4),
            'ci_lo': round(r['ci_lo'], 4),
            'ci_hi': round(r['ci_hi'], 4),
            'pi_lo': round(r['pi_lo'], 4),
            'pi_hi': round(r['pi_hi'], 4),
            'tau2': round(r['tau2'], 4),
            'I2': round(r['I2'], 1),
            'pi_ci_ratio': round(r['pi_ci_ratio'], 2),
            'p_value': round(r['p_value'], 6),
            'discordance': disc,
        }
        results.append(row)

    elapsed = time.time() - t0
    n = len(results)
    if n == 0:
        print("ERROR: No prediction-gap results were produced; aborting export.")
        return None
    print(f"  {n} reviews analyzed in {elapsed:.1f}s")

    # Export
    fields = list(results[0].keys())
    results_path = output_path / 'prediction_gap_results.csv'
    with open(results_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    # Summary
    counts = {}
    for cat in ['FALSE_REASSURANCE', 'CONCORDANT_SIG', 'CONCORDANT_NS', 'HIDDEN_SIGNAL']:
        counts[cat] = sum(1 for r in results if r['discordance'] == cat)

    pi_ci_ratios = [r['pi_ci_ratio'] for r in results if r['pi_ci_ratio'] < 100]
    i2_vals = [r['I2'] for r in results]

    # Among "significant" reviews (CI excludes null), how many have PI crossing null?
    sig_reviews = [r for r in results if r['discordance'] in ('FALSE_REASSURANCE', 'CONCORDANT_SIG')]
    n_sig = len(sig_reviews)
    n_false = counts['FALSE_REASSURANCE']
    pct_false = (n_false / n_sig * 100) if n_sig > 0 else 0

    summary = {
        'n_reviews': n,
        'classification_counts': counts,
        'n_significant': n_sig,
        'n_false_reassurance': n_false,
        'pct_false_reassurance': round(pct_false, 1),
        'pi_ci_ratio': {
            'mean': round(float(np.mean(pi_ci_ratios)), 2),
            'median': round(float(np.median(pi_ci_ratios)), 2),
            'q25': round(float(np.percentile(pi_ci_ratios, 25)), 2),
            'q75': round(float(np.percentile(pi_ci_ratios, 75)), 2),
        },
        'I2_distribution': {
            'mean': round(float(np.mean(i2_vals)), 1),
            'pct_above_50': round(sum(1 for v in i2_vals if v > 50) / n * 100, 1),
            'pct_above_75': round(sum(1 for v in i2_vals if v > 75) / n * 100, 1),
        },
        'elapsed_seconds': round(elapsed, 1),
    }

    summary_path = output_path / 'prediction_gap_summary.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    print()
    print("=" * 50)
    print("HEADLINE RESULTS")
    print("=" * 50)
    for cat, count in counts.items():
        pct = count / n * 100
        print(f"  {cat:22s}: {count:4d} ({pct:5.1f}%)")
    print()
    print(f"  THE PREDICTION GAP:")
    print(f"  Of {n_sig} reviews where the CI excludes the null,")
    print(f"  {n_false} ({pct_false:.1f}%) have prediction intervals that INCLUDE the null.")
    print(f"  -> In these reviews, the treatment may not work in the next clinical setting.")
    print()
    print(f"  Mean PI/CI width ratio: {summary['pi_ci_ratio']['mean']}x")
    print(f"  Median PI/CI width ratio: {summary['pi_ci_ratio']['median']}x")
    print(f"  I2 > 50%: {summary['I2_distribution']['pct_above_50']}% of reviews")

    return results, summary


if __name__ == '__main__':
    run_pipeline()
