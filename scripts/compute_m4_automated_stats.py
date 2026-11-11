import csv
import json
from pathlib import Path
from collections import defaultdict, Counter
import numpy as np
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parent.parent
FINAL_DIR = REPO_ROOT / "experiments" / "t07-final-evaluation-v1"
HUMAN_RESULTS_JSON = REPO_ROOT / "experiments" / "final-human-audit-20261030" / "results" / "analysis_results.json"
RAW_HUMAN_DIR = REPO_ROOT / "experiments" / "final-human-audit-20261030" / "raw_packets"
import argparse
parser = argparse.ArgumentParser(description="Recompute archived metrics without overwriting supplied summaries.")
parser.add_argument("--output-dir", type=Path, required=True)
args = parser.parse_args()
OUT_M4_DIR = args.output_dir.resolve()
if OUT_M4_DIR.exists() and any(OUT_M4_DIR.iterdir()):
    raise SystemExit("Output directory is not empty; choose a new directory.")
OUT_M4_DIR.mkdir(parents=True, exist_ok=True)

# 1. Load per_query_metrics.csv
with open(FINAL_DIR / "per_query_metrics.csv", "r", encoding="utf-8-sig") as f:
    pq_rows = list(csv.DictReader(f))

by_cfg = {"A": {}, "B": {}, "C": {}}
for r in pq_rows:
    by_cfg[r["configuration"]][r["record_id"]] = r

# Load interactions.jsonl
inter = {"A": {}, "B": {}, "C": {}}
for c in ["A", "B", "C"]:
    for line in (FINAL_DIR / c / "interactions.jsonl").read_text(encoding="utf-8").splitlines():
        d = json.loads(line)
        inter[c][d["record_id"]] = d

all_qids = sorted(by_cfg["A"].keys())
print(f"Total unique held-out test queries: {len(all_qids)}")

# Execution dispositions
dispositions = {}
clarification_examples = []
for c in ["A", "B", "C"]:
    cnt = Counter(by_cfg[c][q]["generation_status"] for q in all_qids)
    dispositions[c] = dict(cnt)
    print(f"Dispositions Config {c}: {dict(cnt)}")

for q in all_qids:
    if by_cfg["B"][q]["generation_status"] == "CLARIFICATION_REQUIRED":
        ib = inter["B"][q]
        clarification_examples.append({
            "record_id": q,
            "office": by_cfg["B"][q]["office"],
            "language": by_cfg["B"][q]["language"],
            "query": ib.get("query_text") or ib.get("raw_query") or ib.get("query"),
            "normalized_query": ib.get("normalized_query"),
            "polysemy_flag": ib.get("polysemy_flag"),
            "matched_terms": ib.get("matched_terms") or ib.get("dictionary_matches"),
            "answer": ib.get("response") or ib.get("answer")
        })
print(f"Clarification required in B ({len(clarification_examples)} queries):", [x["record_id"] for x in clarification_examples])

metrics = ["hit_at_1", "hit_at_k", "mrr_at_k", "context_precision", "context_recall", "faithfulness", "answer_relevancy"]

def get_val(cfg, qid, m):
    if m == "hit_at_1":
        v = by_cfg[cfg][qid]["mrr_at_k"]
        if v == "" or v is None:
            return None
        return 1.0 if abs(float(v) - 1.0) < 1e-9 else 0.0
    v = by_cfg[cfg][qid][m]
    if v == "" or v is None:
        return None
    return float(v)

rng = np.random.default_rng(20261030)
N_BOOT = 10000

summary = {
    "dispositions": dispositions,
    "clarification_examples": clarification_examples,
    "all_valid_per_config": {},
    "matched_210_reconciled": {},
    "statistical_tests": {},
    "by_language": {},
    "by_office": {},
    "human_audit_extended": {}
}

print("\n=== ALL-VALID PER-CONFIG MEAN +/- SD ===")
for m in metrics:
    summary["all_valid_per_config"][m] = {}
    for c in ["A", "B", "C"]:
        vals = [get_val(c, q, m) for q in all_qids]
        vals = [v for v in vals if v is not None]
        arr = np.array(vals)
        summary["all_valid_per_config"][m][c] = {
            "n": len(arr),
            "mean": float(np.mean(arr)),
            "sd": float(np.std(arr, ddof=1))
        }
    print(f"{m:18s} | A: {summary['all_valid_per_config'][m]['A']['mean']:.4f} +/- {summary['all_valid_per_config'][m]['A']['sd']:.4f} (n={summary['all_valid_per_config'][m]['A']['n']}) | "
          f"B: {summary['all_valid_per_config'][m]['B']['mean']:.4f} +/- {summary['all_valid_per_config'][m]['B']['sd']:.4f} (n={summary['all_valid_per_config'][m]['B']['n']}) | "
          f"C: {summary['all_valid_per_config'][m]['C']['mean']:.4f} +/- {summary['all_valid_per_config'][m]['C']['sd']:.4f} (n={summary['all_valid_per_config'][m]['C']['n']})")

print("\n=== MATCHED COMPLETE-CASE MEAN +/- SD & STATISTICAL TESTS (Ch 3 Sec 3.2.11) ===")
for m in metrics:
    matched_q = [q for q in all_qids if all(get_val(c, q, m) is not None for c in ["A", "B", "C"])]
    a_arr = np.array([get_val("A", q, m) for q in matched_q])
    b_arr = np.array([get_val("B", q, m) for q in matched_q])
    c_arr = np.array([get_val("C", q, m) for q in matched_q])
    n = len(matched_q)

    summary["matched_210_reconciled"][m] = {
        "n": n,
        "A": {"mean": float(np.mean(a_arr)), "sd": float(np.std(a_arr, ddof=1))},
        "B": {"mean": float(np.mean(b_arr)), "sd": float(np.std(b_arr, ddof=1))},
        "C": {"mean": float(np.mean(c_arr)), "sd": float(np.std(c_arr, ddof=1))},
    }

    try:
        fried_stat, fried_p = stats.friedmanchisquare(a_arr, b_arr, c_arr)
        fried_stat, fried_p = float(fried_stat), float(fried_p)
    except Exception:
        fried_stat, fried_p = 0.0, 1.0

    pairs_res = {}
    boot_idx = rng.integers(0, n, size=(N_BOOT, n))
    for name, y_arr, x_arr in [("B_vs_A", b_arr, a_arr), ("C_vs_A", c_arr, a_arr), ("B_vs_C", b_arr, c_arr)]:
        diff = y_arr - x_arr
        mean_diff = float(np.mean(diff))
        boot_means = diff[boot_idx].mean(axis=1)
        ci_low, ci_high = np.quantile(boot_means, [0.025, 0.975])

        if m in ["hit_at_1", "hit_at_k"]:
            b_cnt = int(np.sum((y_arr == 1.0) & (x_arr == 0.0)))
            c_cnt = int(np.sum((y_arr == 0.0) & (x_arr == 1.0)))
            if b_cnt + c_cnt == 0:
                p_val = 1.0
            else:
                p_val = float(stats.binomtest(min(b_cnt, c_cnt), b_cnt + c_cnt, 0.5, alternative="two-sided").pvalue)
            pairs_res[name] = {
                "test": "McNemar Exact",
                "mean_diff": mean_diff,
                "ci95_low": float(ci_low),
                "ci95_high": float(ci_high),
                "b_y1_x0": b_cnt,
                "c_y0_x1": c_cnt,
                "discordant": b_cnt + c_cnt,
                "p_value": p_val,
                "sig_bonf_00167": bool(p_val < (0.05 / 3.0))
            }
        else:
            nonzero = diff[diff != 0.0]
            if len(nonzero) == 0:
                w_stat, p_val = 0.0, 1.0
            else:
                res_w = stats.wilcoxon(nonzero, zero_method="wilcox", alternative="two-sided")
                w_stat, p_val = float(res_w.statistic), float(res_w.pvalue)
            pairs_res[name] = {
                "test": "Wilcoxon Signed-Rank",
                "mean_diff": mean_diff,
                "ci95_low": float(ci_low),
                "ci95_high": float(ci_high),
                "nonzero_pairs": int(len(nonzero)),
                "w_statistic": w_stat,
                "p_value": p_val,
                "sig_bonf_00167": bool(p_val < (0.05 / 3.0))
            }

    summary["statistical_tests"][m] = {
        "n": n,
        "friedman_chi2": fried_stat,
        "friedman_p": fried_p,
        "pairwise": pairs_res
    }

for lang in ["english", "taglish", "bislish"]:
    summary["by_language"][lang] = {}
    lang_q = [q for q in all_qids if by_cfg["A"][q]["language"] == lang]
    for m in metrics:
        mq = [q for q in lang_q if all(get_val(c, q, m) is not None for c in ["A", "B", "C"])]
        summary["by_language"][lang][m] = {
            "n": len(mq),
            "A": float(np.mean([get_val("A", q, m) for q in mq])),
            "B": float(np.mean([get_val("B", q, m) for q in mq])),
            "C": float(np.mean([get_val("C", q, m) for q in mq])),
            "A_sd": float(np.std([get_val("A", q, m) for q in mq], ddof=1)),
            "B_sd": float(np.std([get_val("B", q, m) for q in mq], ddof=1)),
            "C_sd": float(np.std([get_val("C", q, m) for q in mq], ddof=1)),
        }

offices = sorted({by_cfg["A"][q]["office"] for q in all_qids})
for off in offices:
    summary["by_office"][off] = {}
    off_q = [q for q in all_qids if by_cfg["A"][q]["office"] == off]
    for m in metrics:
        mq = [q for q in off_q if all(get_val(c, q, m) is not None for c in ["A", "B", "C"])]
        summary["by_office"][off][m] = {
            "n": len(mq),
            "A": float(np.mean([get_val("A", q, m) for q in mq])),
            "B": float(np.mean([get_val("B", q, m) for q in mq])),
            "C": float(np.mean([get_val("C", q, m) for q in mq])),
        }

if HUMAN_RESULTS_JSON.exists() and RAW_HUMAN_DIR.exists():
    h_res = json.loads(HUMAN_RESULTS_JSON.read_text(encoding="utf-8"))
    human_desc_with_sd = []
    for row in h_res["descriptives"]:
        samples = []
        for s_val in range(1, 6):
            samples.extend([s_val] * row[f"score_{s_val}"])
        arr = np.array(samples, dtype=float)
        row_copy = dict(row)
        row_copy["sd"] = float(np.std(arr, ddof=1))
        human_desc_with_sd.append(row_copy)

    m1_by_item = defaultdict(dict)
    m2_rel_by_item = defaultdict(dict)
    m2_fai_by_item = defaultdict(dict)
    for rater in ["R01", "R02", "R03"]:
        for mod in ["M1", "M2"]:
            sub = RAW_HUMAN_DIR / f"{rater}-{mod}"
            jf = [sub / f for f in sub.iterdir() if "final" in f.name.lower() and f.suffix == ".json"][0]
            data = json.loads(jf.read_text(encoding="utf-8"))
            for resp in data["records"]:
                iid = resp["answer_id"]
                if mod == "M1":
                    m1_by_item[iid][rater] = int(resp["fidelity_score"])
                else:
                    m2_rel_by_item[iid][rater] = int(resp["relevance_score"])
                    m2_fai_by_item[iid][rater] = int(resp["faithfulness_score"])

    def calc_pairwise_agree(item_dict):
        exact = 0
        adj = 0
        total_pairs = 0
        unanimous = 0
        for iid, rmap in item_dict.items():
            vals = list(rmap.values())
            if len(set(vals)) == 1:
                unanimous += 1
            for i in range(len(vals)):
                for j in range(i + 1, len(vals)):
                    total_pairs += 1
                    if vals[i] == vals[j]:
                        exact += 1
                    if abs(vals[i] - vals[j]) <= 1:
                        adj += 1
        return {
            "items": len(item_dict),
            "total_pairs": total_pairs,
            "exact_pct": 100.0 * exact / total_pairs,
            "adjacent_pct": 100.0 * adj / total_pairs,
            "unanimous_items": unanimous,
            "unanimous_pct": 100.0 * unanimous / len(item_dict)
        }

    agree_stats = {
        "M1_fidelity": calc_pairwise_agree(m1_by_item),
        "M2_relevance": calc_pairwise_agree(m2_rel_by_item),
        "M2_faithfulness": calc_pairwise_agree(m2_fai_by_item)
    }
    summary["human_audit_extended"] = {
        "descriptives_with_sd": human_desc_with_sd,
        "pairwise_agreement": agree_stats
    }

(OUT_M4_DIR / "m4_automated_statistical_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(f"\nSaved complete {OUT_M4_DIR / 'm4_automated_statistical_summary.json'}!")
