"""
Task T06: Retrieval Grid Search on the Development Split.
"""

import os
import json
import pickle
import requests
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss

DEV_BENCHMARK_PATH = "data/benchmark_scenarios_dev.json"
CORPUS_PATH = "data/eboss_corpus_chunks_v1.json"
DICT_PATH = "data/municipal_dictionary_v1.json"
FAISS_INDEX_PATH = "data/faiss_index.bin"
BM25_INDEX_PATH = "data/bm25_index.pkl"
RESULTS_CSV_PATH = "experiments/grid_search_dev_results.csv"
PIPELINE_MANIFEST_PATH = "config/pipeline_manifest.json"

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
MODEL_NAME = "eboss-mistral"
EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

BASELINE_THETA = {"alpha": 0.4, "beta": 0.4, "gamma": 0.2}
K_VALUES = [3, 5]


def load_normalized_dictionary(path: str) -> list:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    entries = []
    if isinstance(raw, dict):
        for term, fields in raw.items():
            entry = dict(fields)
            entry.setdefault("local_term", term)
            entry["english_equivalent"] = entry.get(
                "english_equivalent", entry.get("verified_english_definition", "")
            )
            entries.append(entry)
    else:
        for entry in raw:
            entry = dict(entry)
            entry["english_equivalent"] = entry.get(
                "english_equivalent", entry.get("verified_english_definition", "")
            )
            entries.append(entry)
    return entries


def query_ollama_normalizer(query: str, dictionary_terms: list) -> str:
    relevant_terms = [
        t for t in dictionary_terms if t["local_term"].lower() in query.lower()
    ]
    dict_context = ""
    if relevant_terms:
        dict_context = "Use these standard municipal definitions:\n" + "\n".join(
            [f"- {t['local_term']}: {t['english_equivalent']}" for t in relevant_terms]
        )

    prompt = f"""<s>[INST] You are a professional query normalizer for Davao City eBOSS municipal services.
Translate the following citizen query into concise, formal Philippine legal and procedural English.
Retain all specific office acronyms, fee amounts, and numbers accurately.
Do not add conversational fluff. Output ONLY the translated query.

{dict_context}

Query to normalize: {query} [/INST]"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0, "top_p": 0.0, "num_predict": 150},
    }
    try:
        res = requests.post(OLLAMA_ENDPOINT, json=payload, timeout=60)
        return res.json().get("response", "").strip().replace('"', "")
    except Exception as e:
        print(f"[!] Ollama normalization fallback triggered for '{query}': {e}")
        return query


def min_max_normalize(scores: np.ndarray) -> np.ndarray:
    min_v = np.min(scores)
    max_v = np.max(scores)
    if max_v - min_v < 1e-8:
        return np.zeros_like(scores)
    return (scores - min_v) / (max_v - min_v + 1e-8)


def compute_retrieval_metrics(retrieved_ids: list, ground_truth_ids: list):
    gt = set(ground_truth_ids)
    hits = [1 if cid in gt else 0 for cid in retrieved_ids]

    hit1 = 1.0 if any(hits[:1]) else 0.0
    hit3 = 1.0 if any(hits[:3]) else 0.0
    hit5 = 1.0 if any(hits[:5]) else 0.0

    mrr = 0.0
    for idx, hit in enumerate(hits):
        if hit == 1:
            mrr = 1.0 / (idx + 1)
            break

    running_hits = 0
    precisions = []
    for idx, hit in enumerate(hits):
        if hit == 1:
            running_hits += 1
            precisions.append(running_hits / (idx + 1))
    context_precision = np.mean(precisions) if precisions else 0.0

    return hit1, hit3, hit5, mrr, context_precision


def build_simplex_grid(step: float = 0.1) -> list:
    n = round(1.0 / step)
    grid = []
    for i in range(n + 1):
        for j in range(n + 1 - i):
            k = n - i - j
            a, b, g = round(i * step, 2), round(j * step, 2), round(k * step, 2)
            grid.append((a, b, g))
    return grid


def run_grid_search():
    print("=" * 65)
    print("[*] STARTING TASK T06: RETRIEVAL GRID SEARCH ON DEVELOPMENT SPLIT")
    print("=" * 65)

    with open(DEV_BENCHMARK_PATH, "r", encoding="utf-8") as f:
        dev_scenarios = json.load(f)
    assert len(dev_scenarios) == 30, f"Expected 30 dev scenarios, got {len(dev_scenarios)}"

    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        corpus = json.load(f)
    chunk_ids = [c["chunk_id"] for c in corpus]
    chunk_texts = [c["text_content"] for c in corpus]

    dictionary = load_normalized_dictionary(DICT_PATH)

    print(f"[+] Loaded {len(dev_scenarios)} Dev Groups (90 queries), "
          f"{len(corpus)} corpus chunks, {len(dictionary)} dictionary entries.")

    print("[*] Loading BM25 and FAISS dense indexes...")
    with open(BM25_INDEX_PATH, "rb") as f:
        bm25_data = pickle.load(f)
        bm25 = bm25_data["bm25"]

    faiss_index = faiss.read_index(FAISS_INDEX_PATH)
    embedder = SentenceTransformer(EMBED_MODEL_NAME, device="cpu")

    print("[*] Normalizing 90 development queries (English pass-through, "
          "Taglish/Bislish through eboss-mistral)...")
    normalized_cache = []
    for item in dev_scenarios:
        gid = item["group_id"]
        gt_ids = item["ground_truth_chunk_ids"]
        for lang in ["english", "taglish", "bislish"]:
            raw_q = item["queries"][lang]
            norm_q = raw_q if lang == "english" else query_ollama_normalizer(raw_q, dictionary)
            normalized_cache.append({
                "group_id": gid,
                "language": lang,
                "raw_query": raw_q,
                "normalized_query": norm_q,
                "ground_truth_ids": gt_ids,
            })
    print(f"[SUCCESS] Pre-normalized {len(normalized_cache)} queries.")

    print("[*] Computing retrieval score caches...")
    query_scores = []
    for entry in normalized_cache:
        q_text = entry["normalized_query"]

        tokenized_q = q_text.lower().split()
        bm25_raw = np.array(bm25.get_scores(tokenized_q))
        bm25_norm = min_max_normalize(bm25_raw)

        q_emb = embedder.encode([q_text], normalize_embeddings=True)
        dense_raw = np.zeros(len(corpus))
        D, I = faiss_index.search(q_emb.astype(np.float32), len(corpus))
        for rank, doc_idx in enumerate(I[0]):
            dense_raw[doc_idx] = D[0][rank]
        dense_norm = min_max_normalize(dense_raw)

        matched_keywords = [
            t["local_term"].lower() for t in dictionary
            if t["local_term"].lower() in q_text.lower()
        ]
        dict_boost = np.zeros(len(corpus))
        if matched_keywords:
            for idx, ctext in enumerate(chunk_texts):
                ctext_lower = ctext.lower()
                dict_boost[idx] = sum(1 for kw in matched_keywords if kw in ctext_lower)
            dict_boost = min_max_normalize(dict_boost)

        query_scores.append({
            "entry": entry,
            "bm25": bm25_norm,
            "dense": dense_norm,
            "dict": dict_boost,
        })

    print("\n[*] Provisional baseline theta_0 = (alpha=0.4, beta=0.4, gamma=0.2)...")
    for k in K_VALUES:
        h1s, h3s, h5s, mrrs, cps = [], [], [], [], []
        for item in query_scores:
            fused = (
                BASELINE_THETA["alpha"] * item["bm25"]
                + BASELINE_THETA["beta"] * item["dense"]
                + BASELINE_THETA["gamma"] * item["dict"]
            )
            top_indices = np.argsort(-fused)[:k]
            retrieved_ids = [chunk_ids[i] for i in top_indices]
            h1, h3, h5, mrr, cp = compute_retrieval_metrics(
                retrieved_ids, item["entry"]["ground_truth_ids"]
            )
            h1s.append(h1); h3s.append(h3); h5s.append(h5); mrrs.append(mrr); cps.append(cp)
        print(f"    K={k}: Hit@1={np.mean(h1s):.4f}  Hit@3={np.mean(h3s):.4f}  "
              f"Hit@5={np.mean(h5s):.4f}  MRR={np.mean(mrrs):.4f}  "
              f"ContextPrecision={np.mean(cps):.4f}")

    print("\n[*] Running full grid search sweep over the 2-simplex and K in {3, 5}...")
    grid = build_simplex_grid(step=0.1)
    grid_results = []

    for k in K_VALUES:
        for (a, b, g) in grid:
            h1_list, h3_list, h5_list, mrr_list, cp_list = [], [], [], [], []
            for item in query_scores:
                fused = a * item["bm25"] + b * item["dense"] + g * item["dict"]
                top_indices = np.argsort(-fused)[:k]
                retrieved_ids = [chunk_ids[i] for i in top_indices]
                h1, h3, h5, mrr, cp = compute_retrieval_metrics(
                    retrieved_ids, item["entry"]["ground_truth_ids"]
                )
                h1_list.append(h1); h3_list.append(h3); h5_list.append(h5)
                mrr_list.append(mrr); cp_list.append(cp)

            grid_results.append({
                "top_k": k,
                "alpha_bm25": a,
                "beta_dense": b,
                "gamma_dict": g,
                "mean_hit1": np.mean(h1_list),
                "mean_hit3": np.mean(h3_list),
                "mean_hit5": np.mean(h5_list),
                "mean_mrr": np.mean(mrr_list),
                "mean_context_precision": np.mean(cp_list),
            })

    df = pd.DataFrame(grid_results)
    os.makedirs(os.path.dirname(RESULTS_CSV_PATH), exist_ok=True)
    df.to_csv(RESULTS_CSV_PATH, index=False)

    best_config = df.sort_values(
        by=["mean_context_precision", "mean_hit3", "mean_mrr"], ascending=False
    ).iloc[0]

    print("\n" + "=" * 65)
    print("[SUCCESS] GRID SEARCH COMPLETE")
    print(f"Total Parameter Combinations Evaluated: {len(df)} "
          f"({len(grid)} simplex points x {len(K_VALUES)} K values)")
    print(f"Results Logged to: {RESULTS_CSV_PATH}")
    print("-" * 65)
    print(f"Optimal Top-K              : {int(best_config['top_k'])}")
    print(f"Optimal Alpha (BM25)       : {best_config['alpha_bm25']}")
    print(f"Optimal Beta (Dense)       : {best_config['beta_dense']}")
    print(f"Optimal Gamma (Dict Boost) : {best_config['gamma_dict']}")
    print(f"Best Context Precision     : {best_config['mean_context_precision']:.4f}")
    print(f"Best Hit@3                 : {best_config['mean_hit3']:.4f}")
    print(f"Best MRR                   : {best_config['mean_mrr']:.4f}")
    print("=" * 65)

    manifest = {
        "status": "frozen",
        "task_origin": "T06",
        "optimal_retrieval_weights": {
            "alpha_bm25": float(best_config["alpha_bm25"]),
            "beta_dense": float(best_config["beta_dense"]),
            "gamma_dict": float(best_config["gamma_dict"]),
        },
        "optimal_top_k": int(best_config["top_k"]),
        "retrieval_metrics_dev": {
            "mean_hit1": float(best_config["mean_hit1"]),
            "mean_hit3": float(best_config["mean_hit3"]),
            "mean_hit5": float(best_config["mean_hit5"]),
            "mean_mrr": float(best_config["mean_mrr"]),
            "mean_context_precision": float(best_config["mean_context_precision"]),
        },
        "provisional_baseline_theta0": BASELINE_THETA,
        "models": {"llm": MODEL_NAME, "embedder": EMBED_MODEL_NAME},
        "constraints": {
            "context_budget_k_options": K_VALUES,
            "temperature": 0.0,
            "top_p": 0.0,
            "chunk_tokens": 120,
            "overlap_tokens": 20,
        },
    }
    os.makedirs(os.path.dirname(PIPELINE_MANIFEST_PATH), exist_ok=True)
    with open(PIPELINE_MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"[+] Optimal parameters frozen into: {PIPELINE_MANIFEST_PATH}")


if __name__ == "__main__":
    run_grid_search()
