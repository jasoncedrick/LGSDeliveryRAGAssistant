import os, sys, json, csv, hashlib
from collections import Counter, defaultdict
from pathlib import Path
import numpy as np
from scipy import stats
import krippendorff

REPO_ROOT = Path(__file__).resolve().parent.parent
TRUE_ROOT = REPO_ROOT / "experiments" / "final-human-audit-20261030" / "raw_packets"
FINAL_ARCHIVES = REPO_ROOT / "experiments" / "t07-final-evaluation-v1"
import argparse
parser = argparse.ArgumentParser(description="Recompute supplied human ratings without overwriting imported results.")
parser.add_argument("--output-dir", type=Path, required=True)
args = parser.parse_args()
OUT_DIR = args.output_dir.resolve()
if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
    raise SystemExit("Output directory is not empty; choose a new directory.")
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEED_VAL = "LGS-T08-20261020-v1"

def rank(namespace, value):
    return hashlib.sha256(f"{SEED_VAL}|{namespace}|{value}".encode()).hexdigest()

def records(config):
    return [json.loads(line) for line in
            (FINAL_ARCHIVES / config / "interactions.jsonl").read_text(encoding="utf-8").splitlines()]

archives = {c: {r["question_id"]: r for r in records(c)} for c in "ABC"}

# Build answer_id mapping
mapping = {}
for q, r in archives["A"].items():
    for c in "ABC":
        aid = "R-" + rank("answer-id", q + "|" + c)[:16]
        mapping[aid] = dict(module="M2", answer_id=aid, question_id=q, group_id=r["question_group_id"],
                            configuration=c, category=r["pillar"], language=r["language"])

for q, r in archives["A"].items():
    if r["language"] != "english":
        for c in "BC":
            aid = "N-" + rank("answer-id", q + "|" + c)[:16]
            mapping[aid] = dict(module="M1", answer_id=aid, question_id=q, group_id=r["question_group_id"],
                                configuration=c, category=r["pillar"], language=r["language"])

raters_map = ["R01", "R02", "R03"]

rows = []
for rater in raters_map:
    d1_dir = TRUE_ROOT / f"{rater}-M1"
    p1 = [f for f in os.listdir(d1_dir) if "final" in f.lower() and f.endswith(".json")][0]
    with open(d1_dir / p1, "r", encoding="utf-8") as f:
        d1 = json.load(f)
    for rec in d1["records"]:
        aid = rec["answer_id"]
        k = mapping[aid]
        rows.append(dict(module="M1", dimension="fidelity", rater=rater, answer_id=aid, query_id=rec["query_id"],
                         group_id=k["group_id"], configuration=k["configuration"], language=k["language"],
                         category=k["category"], score=rec["fidelity_score"], no_factual_claims=False))

    d2_dir = TRUE_ROOT / f"{rater}-M2"
    p2 = [f for f in os.listdir(d2_dir) if "final" in f.lower() and f.endswith(".json")][0]
    with open(d2_dir / p2, "r", encoding="utf-8") as f:
        d2 = json.load(f)
    for rec in d2["records"]:
        aid = rec["answer_id"]
        k = mapping[aid]
        no_claims = bool(rec.get("no_factual_claims", False))
        rows.append(dict(module="M2", dimension="relevance", rater=rater, answer_id=aid, query_id=rec["query_id"],
                         group_id=k["group_id"], configuration=k["configuration"], language=k["language"],
                         category=k["category"], score=rec["relevance_score"], no_factual_claims=no_claims))
        rows.append(dict(module="M2", dimension="faithfulness", rater=rater, answer_id=aid, query_id=rec["query_id"],
                         group_id=k["group_id"], configuration=k["configuration"], language=k["language"],
                         category=k["category"], score=rec["faithfulness_score"], no_factual_claims=no_claims))

print(f"Validated total dimension rows: {len(rows)}")
assert len(rows) == 1320

def exact_wilcoxon(d):
    d = np.asarray(d); d = d[d != 0]
    if len(d) == 0: return dict(p_value=1.0, rank_biserial=0.0, nonzero_groups=0, statistic=0.0)
    ranks = stats.rankdata(np.abs(d)); weights = np.rint(2 * ranks).astype(int)
    ways = np.zeros(weights.sum() + 1, dtype=np.int64); ways[0] = 1
    for w in weights:
        old = ways.copy(); ways[w:] += old[:-w]
    observed = abs(int(np.dot(weights, np.sign(d))))
    sums = np.arange(len(ways)) * 2 - weights.sum()
    p = float(ways[np.abs(sums) >= observed].sum() / 2 ** len(d))
    return dict(p_value=p, rank_biserial=float(np.dot(ranks, np.sign(d)) / ranks.sum()),
                nonzero_groups=len(d), statistic=float(min(ranks[d > 0].sum(), ranks[d < 0].sum())))

def alpha(matrix, maximum):
    if np.unique(matrix).size < 2: return None
    return float(krippendorff.alpha(reliability_data=matrix, level_of_measurement="ordinal", value_domain=np.arange(1, maximum + 1)))

groups = sorted({r["group_id"] for r in rows})
categories = {g: next(r["category"] for r in rows if r["group_id"] == g) for g in groups}
strata = [[i for i, g in enumerate(groups) if categories[g] == c] for c in sorted(set(categories.values()))]
rng = np.random.default_rng(20261030)
boot_indices = np.concatenate([rng.choice(s, size=(2000, len(s)), replace=True) for s in strata], axis=1)

print("\n=== TASK T11: INTER-RATER RELIABILITY ===")
reliability_list = []
for module, dim, max_val in [("M1", "fidelity", 5), ("M2", "relevance", 4), ("M2", "faithfulness", 4)]:
    sel = [r for r in rows if r["module"] == module and r["dimension"] == dim]
    ids = sorted({r["answer_id"] for r in sel})
    lookup = {(r["answer_id"], r["rater"]): r for r in sel}
    matrix = np.array([[lookup[i, f"R{n:02d}"]["score"] for i in ids] for n in range(1, 4)])
    est = alpha(matrix, max_val)
    indexes = [[j for j, i in enumerate(ids) if lookup[i, "R01"]["group_id"] == g] for g in groups]
    boot_alpha = [alpha(matrix[:, np.concatenate([indexes[j] for j in sample])], max_val) for sample in boot_indices]
    valid = [v for v in boot_alpha if v is not None]
    low, high = np.quantile(valid, [0.025, 0.975])
    meets = bool(est >= 0.8)
    ci_meets = bool(low >= 0.8)
    rel_item = dict(module=module, dimension=dim, unique_outputs=len(ids), raters=3,
                    ordinal_alpha=float(est), ci95_low=float(low), ci95_high=float(high),
                    point_meets_080=meets, ci_lower_meets_080=ci_meets)
    reliability_list.append(rel_item)
    print(f"{module} {dim}: Alpha = {est:.4f}, 95% CI = [{low:.4f}, {high:.4f}], Meets 0.80? {meets}")

# Descriptive scores
print("\n=== DESCRIPTIVE SCORES ===")
descriptors = []
for module, dim, configs in [("M1", "fidelity", "BC"), ("M2", "relevance", "ABC"), ("M2", "faithfulness", "ABC")]:
    sel = [r for r in rows if r["module"] == module and r["dimension"] == dim]
    for c in configs:
        for lang in ["all"] + sorted({r["language"] for r in sel}):
            ss = [r for r in sel if r["configuration"] == c and (lang == "all" or r["language"] == lang)]
            vals = [r["score"] for r in ss]
            cnt = Counter(vals)
            desc_item = dict(module=module, dimension=dim, configuration=c, language=lang,
                             rating_count=len(vals), unique_outputs=len({r["answer_id"] for r in ss}),
                             mean=float(np.mean(vals)), median=float(np.median(vals)),
                             **{"score_" + str(v): cnt[v] for v in range(1, 6)})
            descriptors.append(desc_item)
            if lang == "all":
                print(f"{module} {dim} Config {c}: Mean = {np.mean(vals):.4f}, Median = {np.median(vals)}")

# Paired comparisons
print("\n=== TASK T12: PAIRED COMPARISONS ===")
comparisons = []
for module, dim, configs in [("M1", "fidelity", "BC"), ("M2", "relevance", "ABC"), ("M2", "faithfulness", "ABC")]:
    sel = [r for r in rows if r["module"] == module and r["dimension"] == dim]
    totals = {c: np.array([sum(r["score"] for r in sel if r["group_id"] == g and r["configuration"] == c) for g in groups]) for c in configs}
    denom = 6 if module == "M1" else 9
    for x, y in ([("B", "C")] if module == "M1" else [("B", "A"), ("C", "A"), ("B", "C")]):
        delta = totals[x] - totals[y]
        means = delta / denom
        test = exact_wilcoxon(delta)
        ci = np.quantile(means[boot_indices].mean(axis=1), [0.025, 0.975])
        nonzero = delta[delta != 0]
        signp = float(stats.binomtest(int((nonzero > 0).sum()), len(nonzero), 0.5).pvalue) if len(nonzero) else 1.0
        comparisons.append(dict(module=module, dimension=dim, contrast=f"{x} minus {y}", scenario_groups=20,
                                mean_difference=float(means.mean()), ci95_low=float(ci[0]), ci95_high=float(ci[1]),
                                positive_groups=int((delta > 0).sum()), negative_groups=int((delta < 0).sum()),
                                tied_groups=int((delta == 0).sum()), sign_test_p_sensitivity=signp,
                                p_value=test["p_value"], rank_biserial=test["rank_biserial"],
                                nonzero_groups=test["nonzero_groups"], statistic=test["statistic"]))

order = sorted(range(len(comparisons)), key=lambda i: comparisons[i]["p_value"])
adjusted = 0
for rank_idx, i in enumerate(order):
    adjusted = max(adjusted, min(1, comparisons[i]["p_value"] * (len(order) - rank_idx)))
    comparisons[i]["holm_p_value"] = adjusted
    comparisons[i]["significant_holm_005"] = bool(adjusted < 0.05)

for comp in comparisons:
    print(f"{comp['module']} {comp['dimension']} {comp['contrast']}: Diff={comp['mean_difference']:+.4f}, 95% CI=[{comp['ci95_low']:+.4f}, {comp['ci95_high']:+.4f}], p={comp['p_value']:.4f}, Holm-p={comp['holm_p_value']:.4f}, Sig={comp['significant_holm_005']}")

# Save CSVs
def write_csv(p, rows_data):
    with open(p, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_data[0].keys()))
        w.writeheader()
        w.writerows(rows_data)

write_csv(OUT_DIR / "reliability.csv", reliability_list)
write_csv(OUT_DIR / "descriptive_scores.csv", descriptors)
write_csv(OUT_DIR / "paired_comparisons.csv", comparisons)

with open(OUT_DIR / "analysis_results.json", "w", encoding="utf-8") as f:
    json.dump(dict(reliability=reliability_list, descriptives=descriptors, comparisons=comparisons), f, indent=2)

print("\nSuccessfully generated analysis_results.json, reliability.csv, descriptive_scores.csv, and paired_comparisons.csv for FINAL HUMAN RATE!")
