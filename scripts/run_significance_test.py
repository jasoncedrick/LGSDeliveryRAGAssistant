"""
Task T12: Statistical Significance Testing on the T07 retrieval-metrics results.

Reads experiments/t07_master_results_test.csv (produced by run_test_comparison.py)
and runs PAIRED significance tests across the three configs on the 210 held-out
test queries. Paired because every config is evaluated on the exact same
queries, not independent samples.

Two comparisons:

  A vs B  - does the full proposed system (dictionary-assisted normalization +
            frozen hybrid fusion) beat the raw BM25 baseline?
  B vs C  - does dictionary injection at translation time help, relative to the
            no-injection ablation? (This is the comparison with the small
            residual gap found in T07 Run 3, after both known bugs were fixed.)

Binary metrics (Hit@1, Hit@3, Hit@5): McNemar's exact test on discordant pairs
(the standard paired test for binary IR metrics -- a paired t-test is NOT
appropriate here since hit/no-hit isn't continuous or normally distributed).

Continuous metrics (MRR, Context Precision): Wilcoxon signed-rank test on
per-query paired differences (non-parametric, doesn't assume the differences
are normally distributed, which they usually aren't for bounded [0,1] scores).

Also reports a query-level bootstrap 95% CI on the mean difference for every
metric as a sanity check alongside the test statistic/p-value.

Caveat (also printed at the end): the 210 queries are not fully independent --
there are 3 per scenario group (same underlying citizen intent, expressed in
English/Taglish/Bislish). These are the standard tests used for this kind of
IR evaluation, but the non-independence is worth noting as a limitation in
Chapter 5, not a reason to distrust a clearly significant (or clearly
non-significant) result.
"""

import numpy as np
import pandas as pd
from scipy import stats

RESULTS_CSV_PATH = "experiments/t07_master_results_test.csv"
OUTPUT_PATH = "experiments/t12_significance_results.csv"
ALPHA = 0.05
N_BOOTSTRAP = 10000
RNG_SEED = 42

METRICS = ["hit1", "hit3", "hit5", "mrr", "context_precision"]
BINARY_METRICS = {"hit1", "hit3", "hit5"}


def load_paired(df: pd.DataFrame, config_x: str, config_y: str, metric: str):
    x = df[df["config"] == config_x].set_index(["group_id", "language"])[metric]
    y = df[df["config"] == config_y].set_index(["group_id", "language"])[metric]
    common = x.index.intersection(y.index)
    return x.loc[common].values.astype(float), y.loc[common].values.astype(float)


def mcnemar_exact(x: np.ndarray, y: np.ndarray):
    """x, y: paired binary (0/1) arrays. Returns (b, c, p_value).
    b = x hit, y miss (x-only wins); c = x miss, y hit (y-only wins)."""
    b = int(np.sum((x == 1) & (y == 0)))
    c = int(np.sum((x == 0) & (y == 1)))
    n = b + c
    if n == 0:
        return b, c, 1.0  # no discordant pairs: configs agree on every query
    result = stats.binomtest(min(b, c), n=n, p=0.5, alternative="two-sided")
    return b, c, result.pvalue


def wilcoxon_signed_rank(x: np.ndarray, y: np.ndarray):
    diffs = y - x
    if np.allclose(diffs, 0):
        return 1.0
    _, p = stats.wilcoxon(x, y, zero_method="wilcox", alternative="two-sided")
    return p


def bootstrap_ci_mean_diff(x: np.ndarray, y: np.ndarray, n_boot=N_BOOTSTRAP, seed=RNG_SEED):
    rng = np.random.default_rng(seed)
    n = len(x)
    diffs = y - x
    boot_means = np.empty(n_boot)
    for i in range(n_boot):
        idx = rng.integers(0, n, size=n)
        boot_means[i] = diffs[idx].mean()
    lo, hi = np.percentile(boot_means, [2.5, 97.5])
    return float(lo), float(hi)


def run_comparison(df: pd.DataFrame, config_x: str, config_y: str, label: str):
    print("\n" + "=" * 78)
    print(f"[*] {label}")
    print(f"    {config_x}  vs  {config_y}")
    print("=" * 78)
    rows = []
    for metric in METRICS:
        x, y = load_paired(df, config_x, config_y, metric)
        n = len(x)
        mean_x, mean_y = x.mean(), y.mean()
        ci_lo, ci_hi = bootstrap_ci_mean_diff(x, y)

        if metric in BINARY_METRICS:
            b, c, p = mcnemar_exact(x, y)
            test_name = "McNemar exact"
            extra = f"(discordant: {config_x}-only={b}, {config_y}-only={c})"
        else:
            p = wilcoxon_signed_rank(x, y)
            test_name = "Wilcoxon signed-rank"
            extra = ""

        sig = "YES" if p < ALPHA else "no"
        print(f"  {metric:18s} mean_x={mean_x:.4f}  mean_y={mean_y:.4f}  "
              f"diff={mean_y - mean_x:+.4f}  95% CI=[{ci_lo:+.4f}, {ci_hi:+.4f}]  "
              f"p={p:.4f}  significant@0.05={sig}  [{test_name}] {extra}")

        rows.append({
            "comparison": label,
            "config_x": config_x,
            "config_y": config_y,
            "metric": metric,
            "n": n,
            "mean_x": mean_x,
            "mean_y": mean_y,
            "mean_diff_y_minus_x": mean_y - mean_x,
            "ci_95_low": ci_lo,
            "ci_95_high": ci_hi,
            "test": test_name,
            "p_value": p,
            "significant_at_0.05": p < ALPHA,
        })
    return rows


def main():
    print("=" * 78)
    print("[*] TASK T12: STATISTICAL SIGNIFICANCE TESTING (T07 RETRIEVAL RESULTS)")
    print("=" * 78)

    df = pd.read_csv(RESULTS_CSV_PATH)

    expected_n = 210
    for cfg in ["A_BM25_Baseline", "B_Proposed", "C_Ablation_NoInjection"]:
        n = (df["config"] == cfg).sum()
        assert n == expected_n, f"Expected {expected_n} rows for {cfg}, found {n}"
    print(f"[+] Loaded {len(df)} rows ({expected_n} queries x 3 configs) from {RESULTS_CSV_PATH}")

    all_rows = []
    all_rows += run_comparison(
        df, "A_BM25_Baseline", "B_Proposed",
        "COMPARISON 1: Does the proposed system beat the raw BM25 baseline?"
    )
    all_rows += run_comparison(
        df, "B_Proposed", "C_Ablation_NoInjection",
        "COMPARISON 2: Does dictionary injection help vs. the no-injection ablation?"
    )

    out = pd.DataFrame(all_rows)
    out.to_csv(OUTPUT_PATH, index=False)

    print("\n" + "=" * 78)
    print(f"[+] Full results saved to: {OUTPUT_PATH}")
    print("=" * 78)
    print("\n[!] Caveat: the 210 test queries are not fully independent (3 per")
    print("    scenario group -- the same underlying citizen intent expressed in")
    print("    English/Taglish/Bislish). These are the standard paired tests for")
    print("    this kind of IR evaluation, but the non-independence is worth noting")
    print("    as a limitation in Chapter 5, not a reason to distrust a clearly")
    print("    significant (or clearly non-significant) result.")


if __name__ == "__main__":
    main()
    