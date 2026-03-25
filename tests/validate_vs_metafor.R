#!/usr/bin/env Rscript
# validate_vs_metafor.R
# Cross-validates Python prediction gap results against R metafor package.
# Selects 10 seeded-random reviews (k >= 5), computes DL random-effects model
# and prediction intervals, compares theta and PI bounds.

library(metafor)

cat("=== PredictionGap: R Cross-Validation vs metafor ===\n\n")

# ---------------------------------------------------------------------------
# 1. Read Python results
# ---------------------------------------------------------------------------
py_results <- read.csv("C:/PredictionGap/data/output/prediction_gap_results.csv",
                       stringsAsFactors = FALSE)
cat("Python results loaded:", nrow(py_results), "rows\n")

# Filter to reviews with k >= 5
py_k5 <- py_results[py_results$k >= 5, ]
cat("Reviews with k >= 5:", nrow(py_k5), "\n")

# ---------------------------------------------------------------------------
# 2. Select 10 reviews (seeded random, seed = 42)
# ---------------------------------------------------------------------------
set.seed(42)
sample_idx <- sample(seq_len(nrow(py_k5)), size = min(10, nrow(py_k5)))
py_sample <- py_k5[sample_idx, ]
cat("Selected", nrow(py_sample), "reviews for validation:\n")
for (i in seq_len(nrow(py_sample))) {
  cat(sprintf("  %2d. %s | %s (k=%d)\n",
              i, py_sample$review_id[i], py_sample$analysis_name[i],
              py_sample$k[i]))
}
cat("\n")

# ---------------------------------------------------------------------------
# 3. Find RDA files for each review
# ---------------------------------------------------------------------------
rda_dir <- "C:/Models/Pairwise70/data/"
rda_files <- list.files(rda_dir, pattern = "\\.rda$", full.names = FALSE)

find_rda <- function(review_id) {
  # Match pattern: CD######_pubN_data.rda
  pattern <- paste0("^", review_id, "_pub\\d+_data\\.rda$")
  matches <- rda_files[grepl(pattern, rda_files)]
  if (length(matches) == 0) return(NA_character_)
  # If multiple versions, take the highest pub number
  pub_nums <- as.integer(sub(paste0(review_id, "_pub(\\d+)_data\\.rda"), "\\1", matches))
  matches[which.max(pub_nums)]
}

# ---------------------------------------------------------------------------
# 4. Helper: select primary analysis from RDA data
# ---------------------------------------------------------------------------
select_analysis <- function(d, target_name, target_k) {
  # Group by Analysis.group + Analysis.number + Analysis.name
  analyses <- unique(d[, c("Analysis.group", "Analysis.number", "Analysis.name")])

  # Compute k for each analysis (counting studies)
  analyses$k <- sapply(seq_len(nrow(analyses)), function(i) {
    sub <- d[d$Analysis.group == analyses$Analysis.group[i] &
             d$Analysis.number == analyses$Analysis.number[i] &
             d$Analysis.name == analyses$Analysis.name[i], ]
    nrow(sub)
  })

  # Try exact name match first
  exact <- analyses[analyses$Analysis.name == target_name, ]
  if (nrow(exact) > 0) {
    # Pick the one with k closest to target
    best <- exact[which.min(abs(exact$k - target_k)), ]
    return(list(group = best$Analysis.group,
                number = best$Analysis.number,
                name = best$Analysis.name,
                k = best$k))
  }

  # Fallback: pick analysis with k closest to target_k
  best <- analyses[which.min(abs(analyses$k - target_k)), ]
  return(list(group = best$Analysis.group,
              number = best$Analysis.number,
              name = best$Analysis.name,
              k = best$k))
}

# ---------------------------------------------------------------------------
# 5. Run validation for each review
# ---------------------------------------------------------------------------
results <- data.frame(
  review_id      = character(),
  analysis_name  = character(),
  python_k       = integer(),
  r_k            = integer(),
  python_theta   = numeric(),
  r_theta        = numeric(),
  theta_diff     = numeric(),
  theta_pass     = logical(),
  python_pi_lo   = numeric(),
  r_pi_lo        = numeric(),
  pi_lo_diff     = numeric(),
  pi_lo_pass     = logical(),
  python_pi_hi   = numeric(),
  r_pi_hi        = numeric(),
  pi_hi_diff     = numeric(),
  pi_hi_pass     = logical(),
  r_tau2         = numeric(),
  overall_pass   = logical(),
  note           = character(),
  stringsAsFactors = FALSE
)

theta_tol <- 1e-3
pi_tol    <- 1e-2

for (i in seq_len(nrow(py_sample))) {
  rid   <- py_sample$review_id[i]
  aname <- py_sample$analysis_name[i]
  py_k  <- py_sample$k[i]
  py_theta  <- py_sample$theta[i]
  py_pi_lo  <- py_sample$pi_lo[i]
  py_pi_hi  <- py_sample$pi_hi[i]
  py_scale  <- py_sample$scale[i]

  cat(sprintf("--- [%d/%d] %s: %s (k=%d) ---\n", i, nrow(py_sample), rid, aname, py_k))

  # Find RDA file

rda_file <- find_rda(rid)
  if (is.na(rda_file)) {
    cat("  SKIP: No RDA file found\n\n")
    results <- rbind(results, data.frame(
      review_id = rid, analysis_name = aname,
      python_k = py_k, r_k = NA_integer_,
      python_theta = py_theta, r_theta = NA_real_, theta_diff = NA_real_, theta_pass = NA,
      python_pi_lo = py_pi_lo, r_pi_lo = NA_real_, pi_lo_diff = NA_real_, pi_lo_pass = NA,
      python_pi_hi = py_pi_hi, r_pi_hi = NA_real_, pi_hi_diff = NA_real_, pi_hi_pass = NA,
      r_tau2 = NA_real_, overall_pass = FALSE, note = "NO_RDA_FILE",
      stringsAsFactors = FALSE
    ))
    next
  }

  # Load RDA
  env <- new.env()
  load(file.path(rda_dir, rda_file), envir = env)
  obj_name <- ls(env)[1]
  d <- get(obj_name, envir = env)

  # Select analysis
  sel <- select_analysis(d, aname, py_k)
  cat(sprintf("  Matched analysis: '%s' (group=%d, number=%d, k=%d)\n",
              sel$name, sel$group, sel$number, sel$k))

  # Extract study-level data
  sub <- d[d$Analysis.group == sel$group &
           d$Analysis.number == sel$number &
           d$Analysis.name == sel$name, ]

  # For ratio scale: compute log(Mean) and SE from CI
  if (py_scale == "ratio") {
    # Filter valid studies
    valid <- sub$Mean > 0 & sub$CI.start > 0 & sub$CI.end > 0
    valid[is.na(valid)] <- FALSE
    sub <- sub[valid, ]

    yi  <- log(sub$Mean)
    sei <- (log(sub$CI.end) - log(sub$CI.start)) / (2 * qnorm(0.975))

    # Filter sei > 0
    keep <- sei > 0
    yi  <- yi[keep]
    sei <- sei[keep]
  } else {
    # For non-ratio (mean difference): use GIV.Mean and GIV.SE if available
    if (!all(is.na(sub$GIV.Mean)) && !all(is.na(sub$GIV.SE))) {
      valid <- !is.na(sub$GIV.Mean) & !is.na(sub$GIV.SE) & sub$GIV.SE > 0
      yi  <- sub$GIV.Mean[valid]
      sei <- sub$GIV.SE[valid]
    } else {
      # Fallback to Mean/CI
      valid <- !is.na(sub$Mean) & !is.na(sub$CI.start) & !is.na(sub$CI.end)
      sub <- sub[valid, ]
      yi  <- sub$Mean
      sei <- (sub$CI.end - sub$CI.start) / (2 * qnorm(0.975))
      keep <- sei > 0
      yi  <- yi[keep]
      sei <- sei[keep]
    }
  }

  r_k <- length(yi)
  cat(sprintf("  Valid studies after filtering: %d\n", r_k))

  if (r_k < 2) {
    cat("  SKIP: Fewer than 2 valid studies\n\n")
    results <- rbind(results, data.frame(
      review_id = rid, analysis_name = aname,
      python_k = py_k, r_k = r_k,
      python_theta = py_theta, r_theta = NA_real_, theta_diff = NA_real_, theta_pass = NA,
      python_pi_lo = py_pi_lo, r_pi_lo = NA_real_, pi_lo_diff = NA_real_, pi_lo_pass = NA,
      python_pi_hi = py_pi_hi, r_pi_hi = NA_real_, pi_hi_diff = NA_real_, pi_hi_pass = NA,
      r_tau2 = NA_real_, overall_pass = FALSE, note = "TOO_FEW_STUDIES",
      stringsAsFactors = FALSE
    ))
    next
  }

  # Run metafor DL model
  tryCatch({
    fit <- rma(yi = yi, sei = sei, method = "DL")
    pred <- predict(fit, level = 0.95)

    r_theta <- as.numeric(fit$beta)
    r_pi_lo <- pred$pi.lb
    r_pi_hi <- pred$pi.ub
    r_tau2  <- fit$tau2

    # Compute differences
    theta_diff <- abs(r_theta - py_theta)
    pi_lo_diff <- abs(r_pi_lo - py_pi_lo)
    pi_hi_diff <- abs(r_pi_hi - py_pi_hi)

    theta_ok <- theta_diff < theta_tol
    pi_lo_ok <- pi_lo_diff < pi_tol
    pi_hi_ok <- pi_hi_diff < pi_tol
    all_ok   <- theta_ok & pi_lo_ok & pi_hi_ok

    status <- ifelse(all_ok, "PASS", "FAIL")
    cat(sprintf("  R theta=%.4f, Python theta=%.4f, diff=%.6f [%s]\n",
                r_theta, py_theta, theta_diff, ifelse(theta_ok, "OK", "FAIL")))
    cat(sprintf("  R PI=[%.4f, %.4f], Python PI=[%.4f, %.4f]\n",
                r_pi_lo, r_pi_hi, py_pi_lo, py_pi_hi))
    cat(sprintf("  PI_lo diff=%.6f [%s], PI_hi diff=%.6f [%s]\n",
                pi_lo_diff, ifelse(pi_lo_ok, "OK", "FAIL"),
                pi_hi_diff, ifelse(pi_hi_ok, "OK", "FAIL")))
    cat(sprintf("  R tau2=%.4f, k_match=%s => %s\n\n",
                r_tau2, ifelse(r_k == py_k, "YES", paste0("NO(", r_k, "vs", py_k, ")")), status))

    note <- ""
    if (r_k != py_k) note <- paste0("k_mismatch:", r_k, "vs", py_k)

    results <- rbind(results, data.frame(
      review_id = rid, analysis_name = aname,
      python_k = py_k, r_k = r_k,
      python_theta = py_theta, r_theta = r_theta, theta_diff = theta_diff, theta_pass = theta_ok,
      python_pi_lo = py_pi_lo, r_pi_lo = r_pi_lo, pi_lo_diff = pi_lo_diff, pi_lo_pass = pi_lo_ok,
      python_pi_hi = py_pi_hi, r_pi_hi = r_pi_hi, pi_hi_diff = pi_hi_diff, pi_hi_pass = pi_hi_ok,
      r_tau2 = r_tau2, overall_pass = all_ok, note = note,
      stringsAsFactors = FALSE
    ))
  }, error = function(e) {
    cat(sprintf("  ERROR: %s\n\n", conditionMessage(e)))
    results <<- rbind(results, data.frame(
      review_id = rid, analysis_name = aname,
      python_k = py_k, r_k = r_k,
      python_theta = py_theta, r_theta = NA_real_, theta_diff = NA_real_, theta_pass = NA,
      python_pi_lo = py_pi_lo, r_pi_lo = NA_real_, pi_lo_diff = NA_real_, pi_lo_pass = NA,
      python_pi_hi = py_pi_hi, r_pi_hi = NA_real_, pi_hi_diff = NA_real_, pi_hi_pass = NA,
      r_tau2 = NA_real_, overall_pass = FALSE, note = paste0("ERROR:", conditionMessage(e)),
      stringsAsFactors = FALSE
    ))
  })
}

# ---------------------------------------------------------------------------
# 6. Summary
# ---------------------------------------------------------------------------
cat("============================================\n")
cat("VALIDATION SUMMARY\n")
cat("============================================\n")
n_run  <- sum(!is.na(results$r_theta))
n_pass <- sum(results$overall_pass, na.rm = TRUE)
n_fail <- n_run - n_pass
n_skip <- sum(is.na(results$r_theta))

cat(sprintf("  Total selected:  %d\n", nrow(results)))
cat(sprintf("  Ran metafor:     %d\n", n_run))
cat(sprintf("  PASS:            %d\n", n_pass))
cat(sprintf("  FAIL:            %d\n", n_fail))
cat(sprintf("  SKIP:            %d\n", n_skip))

if (n_fail > 0) {
  cat("\nFailed reviews:\n")
  fails <- results[!is.na(results$overall_pass) & !results$overall_pass, ]
  for (j in seq_len(nrow(fails))) {
    cat(sprintf("  - %s: theta_diff=%.6f, pi_lo_diff=%.6f, pi_hi_diff=%.6f %s\n",
                fails$review_id[j],
                ifelse(is.na(fails$theta_diff[j]), NA, fails$theta_diff[j]),
                ifelse(is.na(fails$pi_lo_diff[j]), NA, fails$pi_lo_diff[j]),
                ifelse(is.na(fails$pi_hi_diff[j]), NA, fails$pi_hi_diff[j]),
                fails$note[j]))
  }
}

# ---------------------------------------------------------------------------
# 7. Save results
# ---------------------------------------------------------------------------
output_path <- "C:/PredictionGap/data/output/r_crossvalidation.csv"
write.csv(results, output_path, row.names = FALSE)
cat(sprintf("\nResults saved to: %s\n", output_path))
cat(sprintf("Overall: %d/%d PASS (%.0f%%)\n", n_pass, n_run,
            ifelse(n_run > 0, 100 * n_pass / n_run, 0)))
