"""
Generate 4 publication-quality figures for PredictionGap BMJ manuscript.
"""

import csv
import json
import sys
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

OUT_DIR = os.path.join(os.path.dirname(__file__), 'figures')
os.makedirs(OUT_DIR, exist_ok=True)
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data', 'output')

with open(os.path.join(DATA_DIR, 'prediction_gap_results.csv'), encoding='utf-8') as f:
    reviews = list(csv.DictReader(f))

with open(os.path.join(DATA_DIR, 'prediction_gap_summary.json'), encoding='utf-8') as f:
    summary = json.load(f)

for r in reviews:
    r['k_val'] = int(r['k'])
    r['theta_val'] = float(r['theta'])
    r['ci_lo_val'] = float(r['ci_lo'])
    r['ci_hi_val'] = float(r['ci_hi'])
    r['pi_lo_val'] = float(r['pi_lo'])
    r['pi_hi_val'] = float(r['pi_hi'])
    r['tau2_val'] = float(r['tau2'])
    r['I2_val'] = float(r['I2'])
    r['ratio_val'] = float(r['pi_ci_ratio'])
    r['p_val'] = float(r['p_value'])

print(f"Loaded {len(reviews)} reviews")

DISC_COLORS = {
    'CONCORDANT_SIG': '#2ecc71',    # green
    'FALSE_REASSURANCE': '#e74c3c', # red
    'CONCORDANT_NS': '#95a5a6',     # grey
}
DISC_LABELS = {
    'CONCORDANT_SIG': 'Concordant significant\n(CI and PI exclude null)',
    'FALSE_REASSURANCE': 'False reassurance\n(CI excludes null, PI includes null)',
    'CONCORDANT_NS': 'Concordant non-significant\n(CI includes null)',
}

# ─────────────────────────────────────────────────
# FIGURE 1: Classification pie/bar
# ─────────────────────────────────────────────────
print("Generating Figure 1: Classification breakdown...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5), gridspec_kw={'width_ratios': [1, 1.3]})

# Left: Overall breakdown (all 403)
cats = ['CONCORDANT_SIG', 'FALSE_REASSURANCE', 'CONCORDANT_NS']
counts = [summary['classification_counts'][c] for c in cats]
pcts = [c / sum(counts) * 100 for c in counts]
colors = [DISC_COLORS[c] for c in cats]
labels_short = ['Concordant\nsignificant', 'False\nreassurance', 'Concordant\nnon-significant']

bars = ax1.bar(range(3), counts, color=colors, edgecolor='white', width=0.7)
for bar, count, pct in zip(bars, counts, pcts):
    ax1.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5,
             f'{count}\n({pct:.1f}%)', ha='center', va='bottom', fontsize=10, fontweight='bold')
ax1.set_xticks(range(3))
ax1.set_xticklabels(labels_short, fontsize=9)
ax1.set_ylabel('Number of Reviews', fontsize=11)
ax1.set_title('All 403 Reviews', fontsize=12, pad=10)
ax1.set_ylim(0, max(counts) * 1.25)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

# Right: Among 189 significant only (the key finding)
sig_reviews = [r for r in reviews if r['discordance'] in ('CONCORDANT_SIG', 'FALSE_REASSURANCE')]
n_conc = sum(1 for r in sig_reviews if r['discordance'] == 'CONCORDANT_SIG')
n_false = sum(1 for r in sig_reviews if r['discordance'] == 'FALSE_REASSURANCE')

wedges, texts, autotexts = ax2.pie(
    [n_false, n_conc],
    labels=[f'PI includes null\n(false reassurance)\nn={n_false}', f'PI excludes null\n(concordant)\nn={n_conc}'],
    colors=['#e74c3c', '#2ecc71'],
    autopct='%1.1f%%',
    startangle=90,
    textprops={'fontsize': 10},
    pctdistance=0.55,
    explode=(0.05, 0)
)
for t in autotexts:
    t.set_fontweight('bold')
    t.set_fontsize(12)
ax2.set_title(f'Among 189 Significant Reviews:\nThe Prediction Gap', fontsize=12, pad=10)

plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'figure1_classification.png'), dpi=300, bbox_inches='tight')
fig.savefig(os.path.join(OUT_DIR, 'figure1_classification.pdf'), bbox_inches='tight')
print("  Saved figure1_classification.png/pdf")
plt.close(fig)


# ─────────────────────────────────────────────────
# FIGURE 2: PI/CI width ratio distribution
# ─────────────────────────────────────────────────
print("Generating Figure 2: PI/CI width ratio...")

fig, ax = plt.subplots(figsize=(8, 5))

ratios = [r['ratio_val'] for r in reviews if r['ratio_val'] < 15]  # cap outliers for viz
disc_types = [r['discordance'] for r in reviews if r['ratio_val'] < 15]

# Stacked histogram by discordance type
for disc_type, color, label in [
    ('FALSE_REASSURANCE', '#e74c3c', 'False reassurance'),
    ('CONCORDANT_SIG', '#2ecc71', 'Concordant significant'),
    ('CONCORDANT_NS', '#95a5a6', 'Concordant non-significant'),
]:
    vals = [r for r, d in zip(ratios, disc_types) if d == disc_type]
    ax.hist(vals, bins=np.arange(1, 12, 0.5), alpha=0.7, color=color, label=label, edgecolor='white')

ax.axvline(x=1.0, color='black', linestyle='-', linewidth=1, label='PI = CI (no heterogeneity)')
ax.axvline(x=summary['pi_ci_ratio']['median'], color='#e67e22', linestyle='--', linewidth=1.5,
           label=f'Median = {summary["pi_ci_ratio"]["median"]:.2f}x')

ax.set_xlabel('Prediction Interval / Confidence Interval Width Ratio', fontsize=11)
ax.set_ylabel('Number of Reviews', fontsize=11)
ax.set_title('Prediction Intervals Are Typically 2-3x Wider Than Confidence Intervals', fontsize=12, pad=10)
ax.legend(loc='upper right', fontsize=9, framealpha=0.9)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

stats_text = (f"Mean: {summary['pi_ci_ratio']['mean']:.2f}x\n"
              f"Median: {summary['pi_ci_ratio']['median']:.2f}x\n"
              f"IQR: {summary['pi_ci_ratio']['q25']:.2f}-{summary['pi_ci_ratio']['q75']:.2f}x")
ax.text(0.97, 0.65, stats_text, transform=ax.transAxes, fontsize=9,
        va='top', ha='right',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='#cccccc', alpha=0.9))

plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'figure2_pi_ci_ratio.png'), dpi=300, bbox_inches='tight')
fig.savefig(os.path.join(OUT_DIR, 'figure2_pi_ci_ratio.pdf'), bbox_inches='tight')
print("  Saved figure2_pi_ci_ratio.png/pdf")
plt.close(fig)


# ─────────────────────────────────────────────────
# FIGURE 3: False reassurance by I-squared band
# ─────────────────────────────────────────────────
print("Generating Figure 3: False reassurance by I-squared...")

fig, ax = plt.subplots(figsize=(7, 5))

bands = [(0, 25), (25, 50), (50, 75), (75, 100)]
band_labels = ['0-25%', '25-50%', '50-75%', '75-100%']
n_sig_per_band = []
n_false_per_band = []

for lo, hi in bands:
    sig = [r for r in reviews if lo <= r['I2_val'] < hi and r['p_val'] < 0.05]
    false_r = [r for r in sig if r['discordance'] == 'FALSE_REASSURANCE']
    n_sig_per_band.append(len(sig))
    n_false_per_band.append(len(false_r))

pct_false = [f / s * 100 if s > 0 else 0 for f, s in zip(n_false_per_band, n_sig_per_band)]

x = range(4)
bars_sig = ax.bar([i - 0.17 for i in x], n_sig_per_band, width=0.34, color='#3498db',
                  label='All significant reviews', edgecolor='white')
bars_false = ax.bar([i + 0.17 for i in x], n_false_per_band, width=0.34, color='#e74c3c',
                    label='False reassurance', edgecolor='white')

# Add percentage labels
for i, (ns, nf, pct) in enumerate(zip(n_sig_per_band, n_false_per_band, pct_false)):
    ax.text(i + 0.17, nf + 1.5, f'{pct:.0f}%', ha='center', va='bottom',
            fontsize=11, fontweight='bold', color='#c0392b')

ax.set_xticks(range(4))
ax.set_xticklabels([f'I$^2$ {b}' for b in band_labels], fontsize=10)
ax.set_ylabel('Number of Reviews', fontsize=11)
ax.set_xlabel('Heterogeneity (I$^2$)', fontsize=11)
ax.set_title('False Reassurance Rate Increases With Heterogeneity\n'
             'But Is Already 45% at Low Heterogeneity', fontsize=12, pad=10)
ax.legend(loc='upper left', fontsize=9, framealpha=0.9)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'figure3_false_reassurance_by_i2.png'), dpi=300, bbox_inches='tight')
fig.savefig(os.path.join(OUT_DIR, 'figure3_false_reassurance_by_i2.pdf'), bbox_inches='tight')
print("  Saved figure3_false_reassurance_by_i2.png/pdf")
plt.close(fig)


# ─────────────────────────────────────────────────
# FIGURE 4: Exemplar CI vs PI (forest-style comparison)
# ─────────────────────────────────────────────────
print("Generating Figure 4: CI vs PI exemplars...")

fig, ax = plt.subplots(figsize=(9, 7))

# Select 15 exemplar reviews: 5 concordant sig, 5 false reassurance, 5 concordant NS
# Pick reviews with moderate k for visual clarity
def pick_exemplars(disc_type, n=5):
    candidates = [r for r in reviews if r['discordance'] == disc_type and 5 <= r['k_val'] <= 30]
    candidates.sort(key=lambda r: abs(r['theta_val']))  # sort by effect size
    # Spread evenly
    step = max(1, len(candidates) // n)
    return [candidates[i * step] for i in range(min(n, len(candidates)))]

exemplars = []
for dt in ['CONCORDANT_SIG', 'FALSE_REASSURANCE', 'CONCORDANT_NS']:
    exemplars.extend(pick_exemplars(dt, 5))

exemplars.reverse()  # bottom to top

y_positions = list(range(len(exemplars)))
ci_color = '#3498db'
pi_color = '#e74c3c'

for i, r in enumerate(exemplars):
    # PI (wider, behind)
    ax.plot([r['pi_lo_val'], r['pi_hi_val']], [i, i], color=pi_color, linewidth=2.5, alpha=0.5, solid_capstyle='round')
    # CI (narrower, in front)
    ax.plot([r['ci_lo_val'], r['ci_hi_val']], [i, i], color=ci_color, linewidth=4, solid_capstyle='round')
    # Point estimate
    ax.plot(r['theta_val'], i, 'ko', markersize=5, zorder=5)

    # Label
    disc_marker = {'CONCORDANT_SIG': '*', 'FALSE_REASSURANCE': '!', 'CONCORDANT_NS': ''}
    label = f"{r['review_id']} (k={r['k_val']}, I$^2$={r['I2_val']:.0f}%)"
    ax.text(-0.02, i, label, ha='right', va='center', fontsize=7.5, transform=ax.get_yaxis_transform())

# Null line
ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)

# Background bands for classification groups
ax.axhspan(-0.5, 4.5, alpha=0.05, color='#95a5a6')
ax.axhspan(4.5, 9.5, alpha=0.05, color='#e74c3c')
ax.axhspan(9.5, 14.5, alpha=0.05, color='#2ecc71')

ax.text(0.99, 2.0 / len(exemplars), 'Concordant\nnon-significant', transform=ax.transAxes,
        fontsize=8, va='center', ha='right', color='#7f8c8d', style='italic')
ax.text(0.99, 7.0 / len(exemplars), 'False\nreassurance', transform=ax.transAxes,
        fontsize=8, va='center', ha='right', color='#c0392b', style='italic')
ax.text(0.99, 12.0 / len(exemplars), 'Concordant\nsignificant', transform=ax.transAxes,
        fontsize=8, va='center', ha='right', color='#27ae60', style='italic')

# Legend
ci_line = mpatches.Patch(color=ci_color, label='95% Confidence Interval')
pi_line = mpatches.Patch(color=pi_color, alpha=0.5, label='95% Prediction Interval')
ax.legend(handles=[ci_line, pi_line], loc='lower right', fontsize=9, framealpha=0.9)

ax.set_yticks([])
ax.set_xlabel('Effect Estimate (log scale for ratio outcomes)', fontsize=11)
ax.set_title('Confidence Intervals vs Prediction Intervals:\n15 Exemplar Cochrane Meta-Analyses', fontsize=12, pad=10)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_visible(False)

plt.tight_layout()
fig.savefig(os.path.join(OUT_DIR, 'figure4_ci_vs_pi_exemplars.png'), dpi=300, bbox_inches='tight')
fig.savefig(os.path.join(OUT_DIR, 'figure4_ci_vs_pi_exemplars.pdf'), bbox_inches='tight')
print("  Saved figure4_ci_vs_pi_exemplars.png/pdf")
plt.close(fig)

print(f"\nAll figures saved to {OUT_DIR}/")
for f in sorted(os.listdir(OUT_DIR)):
    size = os.path.getsize(os.path.join(OUT_DIR, f))
    print(f"  {f} ({size/1024:.0f} KB)")
