# The Prediction Gap: 70% of Statistically Significant Cochrane Meta-Analyses Have Prediction Intervals That Include the Null

## Authors
Mahmood Ahmad^1

^1 Royal Free Hospital, London, United Kingdom

Correspondence: mahmood.ahmad2@nhs.net | ORCID: 0009-0003-7781-4478

---

## Abstract

**Objective:** To quantify how often the prediction interval of a meta-analysis — which estimates the range of treatment effects expected in a new clinical setting — contradicts the confidence interval that is used to determine statistical significance.

**Design:** Cross-sectional analysis of 403 Cochrane systematic reviews.

**Data source:** Pairwise70 dataset (501 Cochrane reviews with study-level data; 403 eligible with k >= 3 studies).

**Main outcome measures:** For each review, we computed the DerSimonian-Laird pooled effect with 95% confidence interval (CI) and 95% prediction interval (PI). Reviews were classified as: (1) CI excludes null AND PI excludes null (concordant significant); (2) CI excludes null BUT PI includes null (false reassurance — the treatment may not work in the next setting); (3) CI and PI both include null (concordant non-significant).

**Results:** Of 403 reviews, 189 (46.9%) had confidence intervals excluding the null (statistically significant). Of these, 132 (69.8%) had prediction intervals that included the null — meaning the treatment effect, while significant on average, may not apply in a new clinical setting. Only 57 reviews (14.1% of all reviews) had both CI and PI excluding the null. Prediction intervals were on average 3.1 times wider than confidence intervals (median 2.6x). The false reassurance rate increased sharply with heterogeneity: from 42% at I-squared < 25% to 95% at I-squared 50-75%, indicating that even modest heterogeneity is sufficient to invalidate the clinical applicability of a significant pooled estimate.

**Conclusions:** Prediction intervals contradict confidence intervals in 70% of statistically significant Cochrane meta-analyses. Current practice of reporting only confidence intervals creates a "prediction gap" — clinicians and guideline panels are given false reassurance that a treatment effect established "on average" will apply in their clinical setting. Routine reporting of prediction intervals alongside confidence intervals should be mandatory.

---

## Introduction

The confidence interval of a meta-analysis quantifies the precision of the estimated average effect — it answers: "How precisely have we estimated the mean?" [1]. The prediction interval answers a fundamentally different question: "What range of treatment effects would we expect in a new study or clinical setting?" [2,3]. When between-study heterogeneity is present, these two intervals can diverge dramatically, because the prediction interval incorporates both the uncertainty about the mean (the CI component) and the variability of true effects across settings (tau-squared).

IntHout et al. [4] first highlighted this discrepancy, showing in a sample of Cochrane reviews that prediction intervals were often substantially wider than confidence intervals. Riley et al. [2] provided the theoretical framework and advocated for routine reporting. Despite this, prediction intervals remain rarely reported in systematic reviews [5], and clinical guidelines almost universally rely on confidence intervals to judge whether a treatment "works."

We present the first large-scale quantification of the "prediction gap" — the frequency with which prediction intervals contradict the conclusions drawn from confidence intervals across 403 Cochrane systematic reviews.

## Methods

### Data source

We used the Pairwise70 dataset containing 501 Cochrane systematic reviews. Reviews with >= 3 studies in the primary analysis were eligible (n = 403).

### Statistical analysis

For each review, we computed:

**Pooled effect and CI:** DerSimonian-Laird random-effects model with 95% Wald confidence interval.

**Prediction interval:** 95% prediction interval computed as:

PI = theta +/- t_{k-2, 0.025} * sqrt(tau-squared + SE-squared)

where theta is the pooled effect, tau-squared is the between-study variance, SE is the standard error of the pooled effect, and t_{k-2} is the critical value of the t-distribution with k-2 degrees of freedom [2].

**Classification:**
- *Concordant significant:* CI excludes null AND PI excludes null
- *False reassurance:* CI excludes null BUT PI includes null
- *Concordant non-significant:* CI includes null (regardless of PI)

The null value was zero on the log scale for ratio outcomes and zero for difference outcomes.

### PI/CI width ratio

The ratio of PI width to CI width quantifies how much wider the prediction interval is. A ratio of 1.0 means no heterogeneity (PI = CI); larger ratios indicate that the range of expected effects in new settings far exceeds the precision of the average.

## Results

### Overview

Of 403 eligible Cochrane reviews, 189 (46.9%) had 95% CIs that excluded the null (statistically significant at p < 0.05). The remaining 214 (53.1%) were non-significant.

### The prediction gap

Of the 189 reviews with significant CIs, 132 (69.8%) had prediction intervals that included the null (Table 1). Only 57 reviews (14.1% of all 403, 30.2% of significant reviews) had both CI and PI excluding the null — meaning only these reviews provide confident evidence that the treatment will work in the *next* clinical setting.

### PI/CI width ratio

The mean PI/CI width ratio was 3.12 (median 2.62, IQR 1.77-3.77). In 95.3% of reviews, the PI was wider than the CI. In 42.7%, the PI was more than 3 times wider.

### Role of heterogeneity

The false reassurance rate varied with heterogeneity:

| I-squared band | n significant | n false reassurance | % false reassurance |
|---|---|---|---|
| 0-25% | 78 | 33 | 42.3% |
| 25-50% | 36 | 29 | 80.6% |
| 50-75% | 43 | 41 | 95.3% |
| 75-100% | 32 | 29 | 90.6% |

Even at low heterogeneity (I-squared < 25%), 42% of significant CIs were contradicted by their PIs, driven by the additional uncertainty from the t-distribution and small k.

## Discussion

### Summary

We found that prediction intervals contradict confidence intervals in 70% of statistically significant Cochrane meta-analyses. This means that for the majority of treatments deemed "effective" by current meta-analytic standards, there is substantial probability that the treatment will not work — or may even cause harm — in the next clinical setting.

### Implications

This finding has immediate implications for how meta-analyses are reported and interpreted:

1. **For GRADE assessments:** The GRADE framework downgrades for imprecision based on confidence interval width. Our findings suggest that *prediction interval* width should also be considered — a narrow CI with a wide PI is precise about the average but uninformative about what to expect locally.

2. **For clinical guidelines:** Guidelines that state "treatment X reduces mortality (RR 0.85, 95% CI 0.78-0.93)" convey false precision when the prediction interval is 0.55-1.31. The guideline should report both intervals.

3. **For systematic reviewers:** The PRISMA 2020 statement [6] does not require prediction intervals. Our data suggest it should.

4. **For patients:** A patient asking "will this treatment work for me?" cannot be reassured by a confidence interval. The prediction interval is the relevant quantity.

### Strengths and limitations

This is the first large-scale quantification of PI-CI discordance across hundreds of real meta-analyses. Our DerSimonian-Laird pooled estimates were validated against the R `metafor` package (v4.8-0) with agreement within 10^-4 across 10 randomly selected reviews. Prediction intervals were computed using t_{k-2} degrees of freedom following Riley et al. [2]; metafor uses t_{k-1} by default, producing slightly narrower PIs, particularly for small k. This methodological choice makes our false reassurance rates conservative (higher) compared to the metafor convention. Limitations include: (1) PIs assume normally distributed random effects, which may not hold; (2) for small k, PIs are very wide due to the t-distribution, potentially overstating the gap; (3) the DL estimator may underestimate tau-squared, which would underestimate the true prediction gap.

## Conclusions

Prediction intervals include the null in 70% of Cochrane meta-analyses where the confidence interval does not. Only 14% of all reviews provide concordant evidence that the treatment effect will apply in new settings. Routine reporting of prediction intervals should become standard practice.

## Data availability statement

The Pairwise70 dataset is available from [ZENODO_DOI_PLACEHOLDER]. The analysis code, all output data, and an interactive dashboard are available at https://github.com/mahmood726-cyber/prediction-gap.

## Funding

[FUNDING_PLACEHOLDER]

## Competing interests

All authors have completed the ICMJE uniform disclosure form and declare: no support from any organisation for the submitted work; no financial relationships with any organisations that might have an interest in the submitted work; no other relationships or activities that could appear to have influenced the submitted work.

## Patient and public involvement

No patients or members of the public were involved in the design or conduct of this study.

## References

1. Borenstein M, Hedges LV, Higgins JPT, Rothstein HR. Introduction to Meta-Analysis. 2nd ed. Wiley; 2021.
2. Riley RD, Higgins JPT, Deeks JJ. Interpretation of random effects meta-analyses. BMJ. 2011;342:d549.
3. Higgins JPT, Thompson SG, Spiegelhalter DJ. A re-evaluation of random-effects meta-analysis. J R Stat Soc Ser A. 2009;172(1):137-159.
4. IntHout J, Ioannidis JPA, Rovers MM, Goeman JJ. Plea for routinely presenting prediction intervals in meta-analysis. BMJ Open. 2016;6:e010247.
5. Partlett C, Riley RD. Random effects meta-analysis: Coverage performance of 95% confidence and prediction intervals following REML estimation. Stat Med. 2017;36:301-317.
6. Page MJ, McKenzie JE, Bossuyt PM, et al. The PRISMA 2020 statement. BMJ. 2021;372:n71.
