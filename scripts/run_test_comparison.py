"""
Task T07 (retrieval-metrics scope): Evaluate Configurations A, B, and C on the
70 held-out test scenario groups (210 queries), per Chapter 3 Sections 3.4.1
and 3.4.2.

This is the SINGLE-PASS, frozen-pipeline evaluation. It reads the weights
(alpha, beta, gamma) and K frozen by T06 into config/pipeline_manifest.json
and does not tune anything further. Per your methodology's Pipeline Freeze
Point (Section 3.2.8), nothing here should be re-run after seeing results
to "improve" them, unfavorable outcomes get reported, not fixed.

Scope note: this covers only the metrics computable without a generation
module: Hit@1/3/5, MRR, and Context Precision. Answer Relevancy and
Faithfulness need an actual answer-generation step (retrieved context -> LLM
-> final answer) plus a RAGAS wrapper around your local Ollama model, which
is a separate, bigger task deliberately deferred out of this run.

Configurations (Section 3.4.1):
  A - BM25 Baseline: raw, unnormalized query -> BM25-only retrieval.
      No dictionary, no translation, no dense search, no boosting.
  B - Proposed System: dictionary-assisted normalization (via Mistral, with
      glossary injection) -> frozen hybrid fusion (BM25 + FAISS + boost).
  C - Ablation (Injection-Disabled): identical to B, EXCEPT the dictionary
      glossary is not injected into the translation prompt. Isolates what
      the dictionary specifically contributes at translation time (distinct
      from T06's finding that gamma=0 at retrieval time).

Config C uses the SAME QueryNormalizer class, same FEW_SHOT_SYSTEM_PROMPT
(including its two worked few-shot examples), same decoding params as
Config B -- the only difference is that its dictionary is emptied before
use, so scan_query() finds zero matches and glossary_context always
resolves to "None". This isolates dictionary injection as the single
variable that differs between B and C. (An earlier version of this script
used a separate, shorter hand-written prompt for Config C that was also
missing the few-shot examples -- that confounded two variables at once and
has been removed.)
"""

import os
import sys
import json
import pickle
import requests
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss

# Make "src" importable regardless of where this script is invoked from.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.query_normalizer import QueryNormalizer

TEST_BENCHMARK_PATH = "data/benchmark_scenarios_test.json"
CORPUS_PATH = "data/eboss_corpus_chunks_v1.json"
DICT_PATH = "data/municipal_dictionary_v1.json"
FAISS_INDEX_PATH = "data/faiss_index.bin"
BM25_INDEX_PATH = "data/bm25_index.pkl"
MANIFEST_PATH = "config/pipeline_manifest.json"

PER_QUERY_CSV_PATH = "experiments/t07_master_results_test.csv"
SUMMARY_CSV_PATH = "experiments/t07_summary_by_config.csv"

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
MODEL_NAME = "eboss-mistral"
EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def min_max_normalize(scores: np.ndarray) -> np.ndarray:
    min_v = np.min(scores)
    max_v = np.max(scores)
    if max_v - min_v < 1e-8:
        return np.zeros_like(scores)
    return (scores - min_v) / (max_v - min_v + 1e-8)


def compute_retrieval_metrics(retrieved_ids: list, ground_truth_ids: list, k_report=(1, 3, 5)):
    gt = set(ground_truth_ids)
    hits = [1 if cid in gt else 0 for cid in retrieved_ids]

    result = {}
    for k in k_report:
        result[f"hit{k}"] = 1.0 if any(hits[:k]) else 0.0

    mrr = 0.0
    for idx, hit in enumerate(hits):
        if hit == 1:
            mrr = 1.0 / (idx + 1)
            break
    result["mrr"] = mrr

    running_hits = 0
    precisions = []
    for idx, hit in enumerate(hits):
        if hit == 1:
            running_hits += 1
            precisions.append(running_hits / (idx + 1))
    result["context_precision"] = np.mean(precisions) if precisions else 0.0
    return result


def load_normalized_dictionary(path: str) -> list:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    entries = []
    for term, fields in raw.items():
        entry = dict(fields)
        entry.setdefault("local_term", term)
        entries.append(entry)
    return entries


def run_test_evaluation():
    print("=" * 70)
    print("[*] TASK T07 (retrieval-metrics scope): CONFIG A / B / C ON HELD-OUT TEST")
    print("=" * 70)

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    weights = manifest["optimal_retrieval_weights"]
    alpha, beta, gamma = weights["alpha_bm25"], weights["beta_dense"], weights["gamma_dict"]
    top_k = manifest["optimal_top_k"]
    print(f"[+] Frozen from T06: alpha={alpha}, beta={beta}, gamma={gamma}, K={top_k}")

    with open(TEST_BENCHMARK_PATH, "r", encoding="utf-8") as f:
        test_scenarios = json.load(f)
    assert len(test_scenarios) == 70, f"Expected 70 held-out groups, got {len(test_scenarios)}"

    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        corpus = json.load(f)
    chunk_ids = [c["chunk_id"] for c in corpus]
    chunk_texts = [c["text_content"] for c in corpus]

    dictionary = load_normalized_dictionary(DICT_PATH)

    print(f"[+] Loaded {len(test_scenarios)} held-out test groups (210 queries), "
          f"{len(corpus)} corpus chunks.")

    print("[*] Loading BM25 and FAISS indexes, and QueryNormalizer (T03)...")
    with open(BM25_INDEX_PATH, "rb") as f:
        bm25 = pickle.load(f)["bm25"]
    faiss_index = faiss.read_index(FAISS_INDEX_PATH)
    embedder = SentenceTransformer(EMBED_MODEL_NAME, device="cpu")
    normalizer = QueryNormalizer(DICT_PATH)

    # Config C: reuse the SAME QueryNormalizer class (same FEW_SHOT_SYSTEM_PROMPT,
    # same few-shot examples, same decoding params as Config B) but with its
    # dictionary emptied out, so scan_query() never matches anything and
    # glossary_context always resolves to "None". This makes dictionary
    # injection the ONLY variable that differs between B and C.
    normalizer_c = QueryNormalizer(DICT_PATH)
    normalizer_c.dictionary = {}
    normalizer_c.sorted_terms = []

    def score_bm25(text: str) -> np.ndarray:
        tokens = text.lower().split()
        return np.array(bm25.get_scores(tokens))

    def score_dense(text: str) -> np.ndarray:
        emb = embedder.encode([text], normalize_embeddings=True)
        dense = np.zeros(len(corpus))
        D, I = faiss_index.search(emb.astype(np.float32), len(corpus))
        for rank, idx in enumerate(I[0]):
            dense[idx] = D[0][rank]
        return dense

    def score_dict_boost(text: str) -> np.ndarray:
        matched = [t["local_term"].lower() for t in dictionary if t["local_term"].lower() in text.lower()]
        boost = np.zeros(len(corpus))
        if matched:
            for idx, ctext in enumerate(chunk_texts):
                ctext_lower = ctext.lower()
                boost[idx] = sum(1 for kw in matched if kw in ctext_lower)
        return boost

    def retrieve_topk(bm25_raw, dense_raw, boost_raw, a, b, g, k):
        bm25_n = min_max_normalize(bm25_raw)
        dense_n = min_max_normalize(dense_raw) if dense_raw is not None else np.zeros_like(bm25_raw)
        boost_n = min_max_normalize(boost_raw) if boost_raw is not None else np.zeros_like(bm25_raw)
        fused = a * bm25_n + b * dense_n + g * boost_n
        top_idx = np.argsort(-fused)[:k]
        return [chunk_ids[i] for i in top_idx]

    rows = []
    total = len(test_scenarios) * 3
    done = 0

    for sc in test_scenarios:
        gid = sc["group_id"]
        pillar = sc["pillar"]
        gt_ids = sc["ground_truth_chunk_ids"]

        for lang in ["english", "taglish", "bislish"]:
            raw_q = sc["queries"][lang]
            done += 1
            print(f"  [{done}/{total}] {gid} ({lang})")

            # ---- Config A: raw query, BM25 only, no normalization ----
            a_bm25_raw = score_bm25(raw_q)
            a_retrieved = retrieve_topk(a_bm25_raw, None, None, 1.0, 0.0, 0.0, top_k)
            a_metrics = compute_retrieval_metrics(a_retrieved, gt_ids)

            # ---- Config B: full pipeline (dictionary-assisted normalization) ----
            if lang == "english":
                b_query = raw_q
                b_status = "PASSTHROUGH_ENGLISH"
            else:
                norm_result = normalizer.normalize(raw_q)
                if norm_result["status"] == "FALLBACK_TRIGGERED":
                    b_query = raw_q  # ambiguity fallback: no crisp translation available
                    b_status = "FALLBACK_TRIGGERED"
                else:
                    b_query = norm_result["normalized_query"] or raw_q
                    b_status = "SUCCESS"
            b_bm25_raw = score_bm25(b_query)
            b_dense_raw = score_dense(b_query)
            b_boost_raw = score_dict_boost(b_query)
            b_retrieved = retrieve_topk(b_bm25_raw, b_dense_raw, b_boost_raw, alpha, beta, gamma, top_k)
            b_metrics = compute_retrieval_metrics(b_retrieved, gt_ids)

            # ---- Config C: same pipeline, dictionary injection disabled at translation ----
            if lang == "english":
                c_query = raw_q
                c_status = "PASSTHROUGH_ENGLISH"
            else:
                norm_result_c = normalizer_c.normalize(raw_q)
                if norm_result_c["status"] == "FALLBACK_TRIGGERED":
                    # Should not trigger with an empty dictionary (no polysemy
                    # entries left to match), but handle it the same way as B
                    # for symmetry in case that ever changes.
                    c_query = raw_q
                    c_status = "FALLBACK_TRIGGERED"
                else:
                    c_query = norm_result_c["normalized_query"] or raw_q
                    c_status = "SUCCESS"
            c_bm25_raw = score_bm25(c_query)
            c_dense_raw = score_dense(c_query)
            c_boost_raw = score_dict_boost(c_query)  # boost is 0 anyway per T06 (gamma=0)
            c_retrieved = retrieve_topk(c_bm25_raw, c_dense_raw, c_boost_raw, alpha, beta, gamma, top_k)
            c_metrics = compute_retrieval_metrics(c_retrieved, gt_ids)

            for config_name, query_used, status, metrics in [
                ("A_BM25_Baseline", raw_q, "N/A", a_metrics),
                ("B_Proposed", b_query, b_status, b_metrics),
                ("C_Ablation_NoInjection", c_query, c_status, c_metrics),
            ]:
                rows.append({
                    "group_id": gid,
                    "pillar": pillar,
                    "language": lang,
                    "config": config_name,
                    "raw_query": raw_q,
                    "query_used_for_retrieval": query_used,
                    "normalization_status": status,
                    "hit1": metrics["hit1"],
                    "hit3": metrics["hit3"],
                    "hit5": metrics["hit5"],
                    "mrr": metrics["mrr"],
                    "context_precision": metrics["context_precision"],
                })

    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(PER_QUERY_CSV_PATH), exist_ok=True)
    df.to_csv(PER_QUERY_CSV_PATH, index=False)
    print(f"\n[+] Per-query results ({len(df)} rows) saved to: {PER_QUERY_CSV_PATH}")

    summary = df.groupby("config").agg(
        mean_hit1=("hit1", "mean"),
        mean_hit3=("hit3", "mean"),
        mean_hit5=("hit5", "mean"),
        mean_mrr=("mrr", "mean"),
        mean_context_precision=("context_precision", "mean"),
        n_queries=("hit1", "count"),
    ).reset_index()
    summary.to_csv(SUMMARY_CSV_PATH, index=False)

    print("\n" + "=" * 70)
    print("[SUCCESS] T07 RETRIEVAL-METRICS EVALUATION COMPLETE")
    print("=" * 70)
    print(summary.to_string(index=False))
    print(f"\nSummary saved to: {SUMMARY_CSV_PATH}")
    print("=" * 70)


if __name__ == "__main__":
    run_test_evaluation()
    