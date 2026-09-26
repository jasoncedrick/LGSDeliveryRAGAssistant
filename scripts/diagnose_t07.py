import pandas as pd

df = pd.read_csv("experiments/t07_master_results_test.csv")

b = df[df["config"] == "B_Proposed"].set_index(["group_id", "language"])
c = df[df["config"] == "C_Ablation_NoInjection"].set_index(["group_id", "language"])

# Only compare on rows where BOTH configs actually translated (no fallback)
both_translated = b[b["normalization_status"] != "FALLBACK_TRIGGERED"].index

for name, d in [("B (excl. fallback)", b.loc[both_translated]),
                ("C (same rows)", c.loc[both_translated])]:
    print(name, "n=", len(d))
    print(d[["hit1", "hit3", "hit5", "mrr", "context_precision"]].mean())
    print()
    