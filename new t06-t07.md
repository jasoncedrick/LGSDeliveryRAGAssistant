### File Manifest and Repository Checklist for Task T06

Provide your co-member with this exact file checklist. Before initiating any script, verify that their clone of the repository contains the following file structure:

```
LGSDeliveryRAGAssistant/
├── config/
│   └── pipeline_manifest.json          # Target freeze file for optimal weights
├── data/
│   ├── eboss_corpus_chunks_v1.json     # Master corpus (1,031 indexed chunks)
│   ├── municipal_dictionary_v1.json    # Frozen Layer 1 municipal dictionary (150 terms)
│   ├── benchmark_scenarios_dev.json    # 30 Dev Groups / 90 Queries (ACTIVE TARGET)
│   ├── benchmark_scenarios_test.json   # 70 Test Groups / 210 Queries (QUARANTINED)
│   ├── faiss_index.bin                 # Serialized FAISS dense index (MiniLM-L12)
│   └── bm25_index.pkl                  # Serialized BM25 token index
├── scripts/
│   ├── run_eval_harness.py             # Headless grid search & evaluation harness
│   └── verify_complete_benchmark.py   # Integrity check script
└── experiments/
    └── grid_search_dev_results.csv     # Target output logging file

```

> **CRITICAL METHODOLOGICAL RULE FOR CO-MEMBER:** Under Section 3.2.8 of the methodology, `data/benchmark_scenarios_test.json` must remain completely untouched during Task T06. The grid search must execute **strictly** on `data/benchmark_scenarios_dev.json` (90 queries). Loading or inspecting test scenarios will violate the double-blind quarantine protocol and invalidate final findings.
> 
> 

---

### Hardware and Environment Setup (Co-Member's Machine)

Your co-member's machine (Intel Core i7-14700HX, RTX 4060 8 GB VRAM) serves as the primary inference server.

1. **Start Ollama Service with Deterministic Decoding:**
Ensure Ollama has `mistral:7b-instruct` loaded and pinned to greedy decoding:


```bash
ollama pull mistral:7b-instruct
ollama run mistral:7b-instruct

```


*Note: Ollama listens on `http://localhost:11434` by default.*
2. **Install Python Evaluation Dependencies:**
In their active Python virtual environment:
```bash
pip install torch transformers sentence-transformers faiss-cpu rank-bm25 pandas numpy requests

```



---

### The Task T06 Evaluation Harness Script (`scripts/run_eval_harness.py`)

Save the following production evaluation harness into `scripts/run_eval_harness.py`. This script performs a deterministic sweep over the retrieval fusion simplex ($\alpha + \beta + \gamma = 1.0$), evaluates Hit@1, Hit@3, Hit@5, MRR, and Context Precision across all 90 development queries, and exports the ranking results:

```python
import os
import json
import pickle
import requests
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss

# ==========================================
# CONSTANTS & PATHS
# ==========================================
DEV_BENCHMARK_PATH = "data/benchmark_scenarios_dev.json"
CORPUS_PATH = "data/eboss_corpus_chunks_v1.json"
DICT_PATH = "data/municipal_dictionary_v1.json"
FAISS_INDEX_PATH = "data/faiss_index.bin"
BM25_INDEX_PATH = "data/bm25_index.pkl"
RESULTS_CSV_PATH = "experiments/grid_search_dev_results.csv"
PIPELINE_MANIFEST_PATH = "config/pipeline_manifest.json"

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral:7b-instruct"
EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

TOP_K_RETRIEVAL = 5

def query_ollama_normalizer(query: str, dictionary_terms: list) -> str:
    """Translates Bislish/Taglish to English using Mistral 7B greedy decoding."""
    relevant_terms = [t for t in dictionary_terms if t["local_term"].lower() in query.lower()]
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
        "options": {
            "temperature": 0.0,
            "top_p": 0.0,
            "num_predict": 100
        }
    }
    try:
        res = requests.post(OLLAMA_ENDPOINT, json=payload, timeout=30)
        return res.json().get("response", "").strip().replace('"', '')
    except Exception as e:
        print(f"[!] Ollama normalization fallback triggered for '{query}': {e}")
        return query

def min_max_normalize(scores: np.ndarray) -> np.ndarray:
    """Applies stable Min-Max scaling to an array of scores."""
    min_v = np.min(scores)
    max_v = np.max(scores)
    if max_v - min_v < 1e-8:
        return np.zeros_like(scores)
    return (scores - min_v) / (max_v - min_v + 1e-8)

def compute_retrieval_metrics(retrieved_ids: list, ground_truth_ids: list):
    """Computes Hit@1, Hit@3, Hit@5, MRR, and Context Precision."""
    hits = [1 if cid in ground_truth_ids else 0 for cid in retrieved_ids]
    
    hit1 = 1.0 if any(hits[:1]) else 0.0
    hit3 = 1.0 if any(hits[:3]) else 0.0
    hit5 = 1.0 if any(hits[:5]) else 0.0
    
    mrr = 0.0
    for idx, hit in enumerate(hits):
        if hit == 1:
            mrr = 1.0 / (idx + 1)
            break
            
    # Context Precision
    running_hits = 0
    precisions = []
    for idx, hit in enumerate(hits):
        if hit == 1:
            running_hits += 1
            precisions.append(running_hits / (idx + 1))
    context_precision = np.mean(precisions) if precisions else 0.0
    
    return hit1, hit3, hit5, mrr, context_precision

def run_grid_search():
    print("=" * 65)
    print("[*] STARTING TASK T06: RETRIEVAL GRID SEARCH ON DEVELOPMENT SPLIT")
    print("=" * 65)
    
    # 1. Load Data
    with open(DEV_BENCHMARK_PATH, "r", encoding="utf-8") as f:
        dev_scenarios = json.load(f)
    assert len(dev_scenarios) == 30, f"Expected 30 dev scenarios, got {len(dev_scenarios)}"

    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        corpus = json.load(f)
    chunk_ids = [c["chunk_id"] for c in corpus]
    chunk_texts = [c["text_content"] for c in corpus]

    with open(DICT_PATH, "r", encoding="utf-8") as f:
        dictionary = json.load(f)

    print(f"[+] Loaded {len(dev_scenarios)} Dev Groups (90 queries) and {len(corpus)} corpus chunks.")

    # 2. Load Retrieval Indexes
    print("[*] Loading BM25 and FAISS dense indexes...")
    with open(BM25_INDEX_PATH, "rb") as f:
        bm25 = pickle.load(f)
    
    faiss_index = faiss.read_index(FAISS_INDEX_PATH)
    embedder = SentenceTransformer(EMBED_MODEL_NAME, device="cpu")

    # 3. Pre-normalize all 90 queries once and cache
    print("[*] Normalizing 90 development queries through Mistral 7B...")
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
                "ground_truth_ids": gt_ids
            })
    print(f"[SUCCESS] Pre-normalized {len(normalized_cache)} queries.")

    # 4. Precompute raw BM25 and Dense scores for every query
    print("[*] Computing retrieval score caches...")
    query_scores = []
    for entry in normalized_cache:
        q_text = entry["normalized_query"]
        
        # BM25 raw scores
        tokenized_q = q_text.lower().split()
        bm25_raw = np.array(bm25.get_scores(tokenized_q))
        bm25_norm = min_max_normalize(bm25_raw)
        
        # FAISS dense raw scores
        q_emb = embedder.encode([q_text], normalize_embeddings=True)
        dense_raw = np.zeros(len(corpus))
        # Inner product on normalized vectors = cosine similarity
        D, I = faiss_index.search(q_emb.astype(np.float32), len(corpus))
        for rank, doc_idx in enumerate(I[0]):
            dense_raw[doc_idx] = D[0][rank]
        dense_norm = min_max_normalize(dense_raw)
        
        # Dictionary Keyword Match Boost
        dict_boost = np.zeros(len(corpus))
        matched_keywords = [
            t["local_term"].lower() for t in dictionary if t["local_term"].lower() in q_text.lower()
        ]
        if matched_keywords:
            for idx, ctext in enumerate(chunk_texts):
                ctext_lower = ctext.lower()
                matches = sum(1 for kw in matched_keywords if kw in ctext_lower)
                dict_boost[idx] = matches
            dict_boost = min_max_normalize(dict_boost)

        query_scores.append({
            "entry": entry,
            "bm25": bm25_norm,
            "dense": dense_norm,
            "dict": dict_boost
        })

    # 5. Grid Search Loop on the Simplex (alpha + beta + gamma = 1.0)
    print("[*] Running parameter grid search sweep...")
    grid_results = []
    step = 0.1
    for a in np.arange(0.1, 0.9, step):
        for b in np.arange(0.1, 0.9, step):
            for g in np.arange(0.0, 0.4, step):
                if not np.isclose(a + b + g, 1.0):
                    continue
                
                h1_list, h3_list, h5_list, mrr_list, cp_list = [], [], [], [], []
                
                for item in query_scores:
                    fused = a * item["bm25"] + b * item["dense"] + g * item["dict"]
                    top_indices = np.argsort(-fused)[:TOP_K_RETRIEVAL]
                    retrieved_ids = [chunk_ids[i] for i in top_indices]
                    
                    h1, h3, h5, mrr, cp = compute_retrieval_metrics(
                        retrieved_ids, item["entry"]["ground_truth_ids"]
                    )
                    h1_list.append(h1)
                    h3_list.append(h3)
                    h5_list.append(h5)
                    mrr_list.append(mrr)
                    cp_list.append(cp)
                    
                grid_results.append({
                    "alpha_bm25": round(float(a), 2),
                    "beta_dense": round(float(b), 2),
                    "gamma_dict": round(float(g), 2),
                    "mean_hit1": np.mean(h1_list),
                    "mean_hit3": np.mean(h3_list),
                    "mean_hit5": np.mean(h5_list),
                    "mean_mrr": np.mean(mrr_list),
                    "mean_context_precision": np.mean(cp_list)
                })

    df = pd.DataFrame(grid_results)
    os.makedirs(os.path.dirname(RESULTS_CSV_PATH), exist_ok=True)
    df.to_csv(RESULTS_CSV_PATH, index=False)

    # 6. Select Optimal Parameter Set
    best_config = df.sort_values(
        by=["mean_context_precision", "mean_hit3", "mean_mrr"], ascending=False
    ).iloc[0]

    print("\n" + "=" * 65)
    print("[SUCCESS] GRID SEARCH COMPLETE")
    print(f"Total Parameter Combinations Evaluated: {len(df)}")
    print(f"Results Logged to: {RESULTS_CSV_PATH}")
    print("-" * 65)
    print(f"Optimal Alpha (BM25)       : {best_config['alpha_bm25']}")
    print(f"Optimal Beta (Dense)       : {best_config['beta_dense']}")
    print(f"Optimal Gamma (Dict Boost) : {best_config['gamma_dict']}")
    print(f"Best Context Precision     : {best_config['mean_context_precision']:.4f}")
    print(f"Best Hit@3                 : {best_config['mean_hit3']:.4f}")
    print(f"Best MRR                   : {best_config['mean_mrr']:.4f}")
    print("=" * 65)

    # 7. Write to Pipeline Manifest
    manifest = {
        "status": "frozen",
        "task_origin": "T06",
        "optimal_retrieval_weights": {
            "alpha_bm25": float(best_config["alpha_bm25"]),
            "beta_dense": float(best_config["beta_dense"]),
            "gamma_dict": float(best_config["gamma_dict"])
        },
        "retrieval_metrics_dev": {
            "mean_hit1": float(best_config["mean_hit1"]),
            "mean_hit3": float(best_config["mean_hit3"]),
            "mean_hit5": float(best_config["mean_hit5"]),
            "mean_mrr": float(best_config["mean_mrr"]),
            "mean_context_precision": float(best_config["mean_context_precision"])
        },
        "models": {
            "llm": MODEL_NAME,
            "embedder": EMBED_MODEL_NAME
        },
        "constraints": {
            "context_budget_k": TOP_K_RETRIEVAL,
            "temperature": 0.0,
            "top_p": 0.0,
            "chunk_tokens": 120,
            "overlap_tokens": 20
        }
    }
    os.makedirs(os.path.dirname(PIPELINE_MANIFEST_PATH), exist_ok=True)
    with open(PIPELINE_MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"[+] Optimal parameters frozen into: {PIPELINE_MANIFEST_PATH}")

if __name__ == "__main__":
    run_grid_search()

```

---

### Step-by-Step Instructions to Send to Your Co-Member

Send these instructions directly to your co-member:

1. **Pull and Sync the Codebase:**
```bash
git pull origin main

```


2. **Verify That Ollama is Running:**
```bash
ollama list

```


*Confirm `mistral:7b-instruct` is displayed.*
3. **Execute Pre-Flight Integrity Check:**
```bash
python scripts/verify_complete_benchmark.py

```


Must show 30 dev groups and 70 held-out test groups with zero errors.


4. **Execute the Grid Search Optimization:**
```bash
python scripts/run_eval_harness.py

```


*Expected runtime: 3 to 5 minutes on the i7-14700HX / RTX 4060.*
5. **Commit the Results:**
Once the run displays `[SUCCESS] GRID SEARCH COMPLETE`, push the generated results:
```bash
git add config/pipeline_manifest.json experiments/grid_search_dev_results.csv
git commit -m "feat(eval): complete T06 grid search and freeze optimal retrieval weights"
git push origin main

```



After your co-member pushes these two files, Task T06 is 100% complete, your pipeline weights are formally frozen, and you are ready to evaluate Configurations A, B, and C on the quarantined 70 test groups (Task T07).