# The Prediction Gap

Can the pooled effect from a statistically significant meta-analysis be expected to apply in the next clinical setting? We computed DerSimonian-Laird random-effects pooled estimates with both confidence and prediction intervals for 403 eligible Cochrane systematic reviews from the Pairwise70 dataset. For each review, the prediction interval was compared against the CI to classify concordance, using the t-distribution with k minus two degrees of freedom as the critical value. Of the 189 reviews with a 95% CI excluding the null, 132 had a prediction interval including the null, yielding a median false reassurance rate of 69.8%. The mean prediction-interval-to-confidence-interval width ratio was 3.12, and discordance rose sharply from 42% at low heterogeneity to 95% at moderate heterogeneity. Seven in ten significant meta-analyses provide misleading confidence that the average treatment effect will replicate in new clinical settings. However, this analysis is limited to ratio and difference outcomes and cannot address heterogeneity arising from unreported clinical or methodological moderators.

**Live dashboard:** <https://mahmood726-cyber.github.io/predictiongap/>

## Run

Open `index.html` (or `index.html`) in any modern browser. No build step.

For local development:

```bash
python -m http.server 8000
# then open http://localhost:8000/
```

## Test

```bash
python -m pytest -q
```

The suite under `tests/` includes 1 test file(s).

## Repo layout

| Path | Purpose |
|---|---|
| `index.html` | the dashboard (main artifact) |
| `index.html` | landing page |
| `tests/` | pytest tests |
| `e156-submission/` | E156 micro-paper bundle |
| `E156-PROTOCOL.md` | project metadata (E156 entry #136) |

## License

See `LICENSE` (MIT).
