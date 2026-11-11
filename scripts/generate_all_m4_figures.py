import json
import shutil
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
M4_DIR = REPO_ROOT / "results" / "figures"
HUMAN_FIGS_DIR = REPO_ROOT / "experiments" / "final-human-audit-20261030" / "results" / "figures"

for d in [M4_DIR, HUMAN_FIGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

auto = json.loads((REPO_ROOT / "results" / "m4_automated_statistical_summary.json").read_text(encoding="utf-8"))
human = json.loads((REPO_ROOT / "experiments" / "final-human-audit-20261030" / "results" / "analysis_results.json").read_text(encoding="utf-8"))

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.edgecolor": "#333333",
    "axes.linewidth": 0.85,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

COL_A = "#43566b"  # Slate Navy (Baseline A)
COL_B = "#167d8d"  # Deep Teal (Proposed B)
COL_C = "#b06a35"  # Warm Ochre (Ablation C)

def save_all(fig, name, include_human_dir=False):
    targets = [M4_DIR]
    if include_human_dir:
        targets.append(HUMAN_FIGS_DIR)
    for t in targets:
        fig.savefig(t / f"{name}.pdf", bbox_inches="tight")
        fig.savefig(t / f"{name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Generated {name}.pdf & .png")

def plot_heldout_architecture_comparison():
    metrics_order = [
        ("hit_at_1", "Hit@1\n(n=210)"),
        ("hit_at_k", "Hit@3\n(n=210)"),
        ("mrr_at_k", "MRR@3\n(n=210)"),
        ("context_precision", "Context Prec.\n(n=202)"),
        ("context_recall", "Context Rec.\n(n=202)"),
        ("faithfulness", "Faithfulness\n(n=188)"),
        ("answer_relevancy", "Answer Rel.\n(n=202)"),
    ]
    a_vals = [auto["matched_210_reconciled"][k]["A"]["mean"] for k, _ in metrics_order]
    b_vals = [auto["matched_210_reconciled"][k]["B"]["mean"] for k, _ in metrics_order]
    c_vals = [auto["matched_210_reconciled"][k]["C"]["mean"] for k, _ in metrics_order]

    x = np.arange(len(metrics_order))
    w = 0.26

    fig, ax = plt.subplots(figsize=(12.5, 4.6), dpi=300)
    b1 = ax.bar(x - w, a_vals, w, label="Config A (BM25 Sparse Baseline)", color=COL_A, edgecolor="black", linewidth=0.7)
    b2 = ax.bar(x,     b_vals, w, label="Config B (Proposed Dictionary-Assisted Hybrid)", color=COL_B, edgecolor="black", linewidth=0.7)
    b3 = ax.bar(x + w, c_vals, w, label="Config C (Ablation: No Dictionary Injection)", color=COL_C, edgecolor="black", linewidth=0.7)

    for bars in [b1, b2, b3]:
        for bar in bars:
            h = bar.get_height()
            ax.annotate(f"{h:.3f}", xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 3), textcoords="offset points",
                        ha="center", va="bottom", fontsize=7.5, fontweight="bold", rotation=90)

    ax.set_xticks(x)
    ax.set_xticklabels([lbl for _, lbl in metrics_order], fontsize=9.5, fontweight="bold")
    ax.set_ylim(0, 1.18)
    ax.set_ylabel("Mean Metric Score [0.0 – 1.0]", fontsize=10, fontweight="bold")
    ax.set_title("Unseen Held-Out Test Set Evaluation Across Comparative Configurations (70 Scenario Groups / 210 Queries)",
                 fontsize=11.5, fontweight="bold", pad=14)
    ax.legend(loc="upper center", ncol=3, fontsize=8.8, frameon=True)
    ax.grid(axis="y", linestyle="--", alpha=0.45)

    plt.tight_layout()
    save_all(fig, "fig_heldout_architecture_comparison")

def plot_dev_vs_heldout_comparison():
    labels = ["Hit@3", "MRR@3", "Context Precision", "Context Recall", "Faithfulness", "Answer Relevancy"]
    dev_b = [0.7000, 0.6167, 0.9408, 0.9125, 0.8174, 0.5779]
    test_b = [
        auto["matched_210_reconciled"]["hit_at_k"]["B"]["mean"],
        auto["matched_210_reconciled"]["mrr_at_k"]["B"]["mean"],
        auto["matched_210_reconciled"]["context_precision"]["B"]["mean"],
        auto["matched_210_reconciled"]["context_recall"]["B"]["mean"],
        auto["matched_210_reconciled"]["faithfulness"]["B"]["mean"],
        auto["matched_210_reconciled"]["answer_relevancy"]["B"]["mean"],
    ]

    x = np.arange(len(labels))
    w = 0.34

    fig, ax = plt.subplots(figsize=(10.8, 4.6), dpi=300)
    r1 = ax.bar(x - w/2, dev_b, w, label="Development Split (30 Groups / 90 Queries)", color="#5b8c99", edgecolor="black", linewidth=0.7)
    r2 = ax.bar(x + w/2, test_b, w, label="Unseen Held-Out Test Split (70 Groups / 210 Queries)", color=COL_B, edgecolor="black", linewidth=0.7)

    for bars in [r1, r2]:
        for bar in bars:
            h = bar.get_height()
            ax.annotate(f"{h:.4f}", xy=(bar.get_x() + bar.get_width()/2, h),
                        xytext=(0, 3), textcoords="offset points",
                        ha="center", va="bottom", fontsize=7.8, fontweight="bold")

    for i, (dv, tv) in enumerate(zip(dev_b, test_b)):
        delta = tv - dv
        ax.annotate(f"Δ={delta:+.3f}", xy=(x[i], max(dv, tv) + 0.085),
                    ha="center", fontsize=8, fontweight="bold", color="#222222",
                    bbox=dict(boxstyle="round,pad=0.22", fc="#f4f6f8", ec="#bbbbbb", lw=0.7))

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9.5, fontweight="bold")
    ax.set_ylim(0, 1.24)
    ax.set_ylabel("Configuration B Mean Score", fontsize=10, fontweight="bold")
    ax.set_title("Generalization Stability of Configuration B: Development Benchmark vs. Unseen Held-Out Test Set",
                 fontsize=11, fontweight="bold", pad=12)
    ax.legend(loc="upper center", ncol=2, fontsize=9, frameon=True)
    ax.grid(axis="y", linestyle="--", alpha=0.45)

    plt.tight_layout()
    save_all(fig, "fig_dev_vs_heldout_comparison")

def get_h_desc(mod, dim, cfg, lang):
    return next(r for r in human["descriptives"]
                if r["module"] == mod and r["dimension"] == dim and r["configuration"] == cfg and r["language"] == lang)

def plot_human_language_breakdown():
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.4), dpi=300)

    ax = axes[0]
    l_m1 = ["taglish", "bislish"]
    lbl_m1 = ["Taglish\n(N=60/cfg)", "Bislish\n(N=60/cfg)"]
    x = np.arange(2)
    w = 0.30
    b_m1 = [get_h_desc("M1", "fidelity", "B", l)["mean"] for l in l_m1]
    c_m1 = [get_h_desc("M1", "fidelity", "C", l)["mean"] for l in l_m1]
    r1 = ax.bar(x - w/2, b_m1, w, label="Config B (Proposed)", color=COL_B, edgecolor="black", linewidth=0.7)
    r2 = ax.bar(x + w/2, c_m1, w, label="Config C (No Injection)", color=COL_C, edgecolor="black", linewidth=0.7)
    for bars in [r1, r2]:
        for bar in bars:
            h = bar.get_height()
            ax.annotate(f"{h:.4f}", xy=(bar.get_x() + bar.get_width()/2, h),
                        xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(lbl_m1, fontsize=9.5, fontweight="bold")
    ax.set_ylim(0, 5.55)
    ax.set_ylabel("Mean Fidelity (1–5 Likert Scale)", fontsize=9.5, fontweight="bold")
    ax.set_title("A. Module 1: Normalization Fidelity\nby Code-Switched Dialect", fontsize=10.5, fontweight="bold", pad=10)
    ax.legend(loc="lower right", fontsize=8, frameon=True)
    ax.grid(axis="y", linestyle="--", alpha=0.45)

    ax = axes[1]
    l_m2 = ["english", "taglish", "bislish"]
    lbl_m2 = ["English\n(N=60)", "Taglish\n(N=60)", "Bislish\n(N=60)"]
    x2 = np.arange(3)
    w2 = 0.25
    a_rel = [get_h_desc("M2", "relevance", "A", l)["mean"] for l in l_m2]
    b_rel = [get_h_desc("M2", "relevance", "B", l)["mean"] for l in l_m2]
    c_rel = [get_h_desc("M2", "relevance", "C", l)["mean"] for l in l_m2]
    ra = ax.bar(x2 - w2, a_rel, w2, label="Config A (BM25)", color=COL_A, edgecolor="black", linewidth=0.7)
    rb = ax.bar(x2,      b_rel, w2, label="Config B (Proposed)", color=COL_B, edgecolor="black", linewidth=0.7)
    rc = ax.bar(x2 + w2, c_rel, w2, label="Config C (No Injection)", color=COL_C, edgecolor="black", linewidth=0.7)
    for bars in [ra, rb, rc]:
        for bar in bars:
            h = bar.get_height()
            ax.annotate(f"{h:.2f}", xy=(bar.get_x() + bar.get_width()/2, h),
                        xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=7.8, fontweight="bold")
    ax.set_xticks(x2)
    ax.set_xticklabels(lbl_m2, fontsize=9.5, fontweight="bold")
    ax.set_ylim(0, 4.45)
    ax.set_ylabel("Mean Relevance (1–4 Likert Scale)", fontsize=9.5, fontweight="bold")
    ax.set_title("B. Module 2: Answer Relevance\nAcross All Three Dialects", fontsize=10.5, fontweight="bold", pad=10)
    ax.legend(loc="lower right", fontsize=8, frameon=True)
    ax.grid(axis="y", linestyle="--", alpha=0.45)

    ax = axes[2]
    a_fai = [get_h_desc("M2", "faithfulness", "A", l)["mean"] for l in l_m2]
    b_fai = [get_h_desc("M2", "faithfulness", "B", l)["mean"] for l in l_m2]
    c_fai = [get_h_desc("M2", "faithfulness", "C", l)["mean"] for l in l_m2]
    fa = ax.bar(x2 - w2, a_fai, w2, label="Config A (BM25)", color=COL_A, edgecolor="black", linewidth=0.7)
    fb = ax.bar(x2,      b_fai, w2, label="Config B (Proposed)", color=COL_B, edgecolor="black", linewidth=0.7)
    fc = ax.bar(x2 + w2, c_fai, w2, label="Config C (No Injection)", color=COL_C, edgecolor="black", linewidth=0.7)
    for bars in [fa, fb, fc]:
        for bar in bars:
            h = bar.get_height()
            ax.annotate(f"{h:.2f}", xy=(bar.get_x() + bar.get_width()/2, h),
                        xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=7.8, fontweight="bold")
    ax.set_xticks(x2)
    ax.set_xticklabels(lbl_m2, fontsize=9.5, fontweight="bold")
    ax.set_ylim(0, 4.45)
    ax.set_ylabel("Mean Faithfulness (1–4 Likert Scale)", fontsize=9.5, fontweight="bold")
    ax.set_title("C. Module 2: Factual Faithfulness\nAcross All Three Dialects", fontsize=10.5, fontweight="bold", pad=10)
    ax.legend(loc="lower right", fontsize=8, frameon=True)
    ax.grid(axis="y", linestyle="--", alpha=0.45)

    plt.tight_layout()
    save_all(fig, "figure_4_5_language_breakdown", include_human_dir=True)

if __name__ == "__main__":
    plot_heldout_architecture_comparison()
    plot_dev_vs_heldout_comparison()
    plot_human_language_breakdown()
    print("\nALL FIGURES GENERATED IN results/figures/!")
