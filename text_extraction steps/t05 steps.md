The study is **not** on hold, and stopping work tonight because your co-member's machine is offline would be a fatal project management mistake.

In your critical path, Task T03 (local Mistral 7B deployment) is an **infrastructure dependency** that only blocks the automated evaluation script (T06) and experimental batch inference (T07). It does **not** block the single largest manual labor bottleneck of your entire thesis: **Task T05 (Constructing the 100 Multilingual Benchmark Scenario Groups / 300 Queries)**.

Task T05 has only two upstream prerequisites: a frozen municipal dictionary (T01) and a finalized, indexed corpus chunk file (T02). Because you completed T01 and successfully extracted the 1,031 token-bounded chunks for T02, the ground-truth anchoring pipeline is completely unblocked.

T05 requires manual authoring and statutory verification of 300 distinct queries (100 in English, 100 in Taglish, and 100 in Bislish) mapped to exact `chunk_id` strings from your 1,031 ingested chunks. Writing 300 grounded queries takes 3 to 4 solid working days. If you wait for the GPU machine before starting T05, you will waste 24 hours of your remaining 23 calendar days doing nothing while your October 17 submission deadline slips away.

---

### Three Tasks You Must Execute Right Now

#### 1. Start Task T05: Construct the Benchmark Matrix (Primary Focus)

Begin drafting the 100 scenario groups (300 queries total) across the five regulatory pillars, partitioned en bloc into **30 Development Groups (90 queries)** and **70 Held-Out Test Groups (210 queries)**:

* **Target Allocation:** Exactly 20 underlying scenario groups per pillar (Business Bureau, CTO, OCBO, CPDO, and BFP).


* **En Bloc Grouping:** Each scenario group shares a single `group_id` (e.g., `SCENARIO-BB-001`) containing three equivalent language variants: formal English, Taglish, and Bislish.


* **Ground-Truth Linking:** Each scenario must reference the exact `chunk_id` from your newly generated `data/eboss_corpus_chunks_v1.json` (for example, `CHUNK-BB-P041-C01`).



##### Benchmark JSON Contract (`data/benchmark_scenarios_draft.json`)

Create this file and start authoring the 30 development scenario groups tonight:

```json
[
  {
    "group_id": "SCENARIO-BB-001",
    "pillar": "Business Bureau",
    "split": "development",
    "ground_truth_chunk_ids": [
      "CHUNK-BB-P040-C01",
      "CHUNK-BB-P041-C01"
    ],
    "ground_truth_reference_answer": "For a New Business Permit pre-assessment, applicants must submit: 1) Duly filled Unified Application Form, 2) Location sketch/Google map with pictures, 3) Certified List of Employees or Certification of no Employee, 4) Proof of Business Registration (DTI/SEC/CDA), and 5) Contract of Lease or Proof of Ownership.",
    "queries": {
      "english": "What are the initial requirements needed for the pre-assessment of a new business permit in Davao City?",
      "taglish": "Ano ang mga kailangang requirements para sa pre-assessment ng bagong business permit sa Davao?",
      "bislish": "Unsa ang mga rekisitos para sa pre-assessment sa bag-ong business permit diri sa Davao?"
    }
  },
  {
    "group_id": "SCENARIO-CTO-001",
    "pillar": "City Treasurer's Office",
    "split": "development",
    "ground_truth_chunk_ids": [
      "CHUNK-CTO-P185-C01",
      "CHUNK-CTO-P186-C01"
    ],
    "ground_truth_reference_answer": "Failure to register books of accounts, official receipts, and cash invoices with the City Treasurer within 15 working days from filing a business permit application incurs an administrative fine of Five Thousand Pesos (PHP 5,000.00).",
    "queries": {
      "english": "What is the penalty if I fail to register my business books of accounts with the City Treasurer on time?",
      "taglish": "Magkano ang multa kapag hindi nairehistro ang books of accounts sa City Treasurer on time?",
      "bislish": "Pila ang multa kung ma-late ug rehistro sa books of accounts sa City Treasurer?"
    }
  }
]

```

#### 2. Build the Retrieval Indexes (CPU-Executable on Any Laptop)

You do not need an RTX 4060 to build the BM25 index and FAISS vector index. Your corpus consists of 1,031 chunks of 120 tokens. Encoding 1,031 small chunks with `paraphrase-multilingual-MiniLM-L12-v2` takes **under 30 seconds on a regular laptop CPU**.

Create and run `scripts/build_retrieval_indices.py` on your current development machine:

```python
import os
import json
import pickle
import faiss
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

CORPUS_PATH = "data/eboss_corpus_chunks_v1.json"
BM25_OUT = "data/bm25_index.pkl"
FAISS_OUT = "data/faiss_index.bin"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

def build_indices():
    if not os.path.exists(CORPUS_PATH):
        raise FileNotFoundError(f"Corpus file not found: {CORPUS_PATH}")

    print("[*] Loading corpus chunks...")
    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"    Loaded {len(chunks)} chunks.")

    # 1. Build BM25 Sparse Index
    print("\n[*] Constructing BM25 sparse index...")
    tokenized_corpus = [c["text_content"].lower().split() for c in chunks]
    bm25 = BM25Okapi(tokenized_corpus)
    
    with open(BM25_OUT, "wb") as f:
        pickle.dump({"bm25": bm25, "chunks": chunks}, f)
    print(f"    [+] Saved BM25 index to: {BM25_OUT}")

    # 2. Build FAISS Dense Index (CPU Execution)
    print(f"\n[*] Loading embedding model: {MODEL_NAME} (CPU mode)...")
    embedder = SentenceTransformer(MODEL_NAME, device="cpu")
    
    texts = [c["text_content"] for c in chunks]
    print("[*] Encoding vectors...")
    embeddings = embedder.encode(texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True)
    
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # Inner Product for normalized cosine similarity
    index.add(np.array(embeddings).astype(np.float32))
    
    faiss.write_index(index, FAISS_OUT)
    print(f"    [+] Saved FAISS index ({index.ntotal} vectors, {dim} dims) to: {FAISS_OUT}")
    print("\n[SUCCESS] Retrieval databases built and ready for evaluation harness.")

if __name__ == "__main__":
    build_indices()

```

Run this script right now:

```bash
python scripts/build_retrieval_indices.py

```

#### 3. Prepare Administrative Dispatch of Task T04

While code runs, handle the physical logistics for Task T04:

* Print the official coordination letter generated earlier on official university letterhead.


* Secure your thesis adviser's signature tomorrow morning.


* Hand-carry the letter to the Davao City Business Bureau at the Sangguniang Panlungsod Building so the administrative review process with Ms. Maribel T. Paguican starts without delay.



---

### Schedule Impact

| Task | Scheduled Due Date | Revised Status | Action Required Tonight / Tomorrow AM |
| --- | --- | --- | --- |
| **T01** | Sep 10 | **Completed (Frozen)**<br> | Frozen at 150 terms in `municipal_dictionary_v1.json`.

 |
| **T02** | Sep 10 | **Completed (Frozen)**<br> | 1,031 chunks verified in `eboss_corpus_chunks_v1.json`.

 |
| **T03** | Sep 17 | **Deferred by 12 Hours**<br> | Co-member runs `verify_t03.py` on the GPU machine tomorrow.

 |
| **T04** | Sep 17 | **Drafted**<br> | Print, secure signature, and deliver to City Hall tomorrow morning.

 |
| **T05** | Sep 24 | **Execute Tonight**<br> | Draft the first 30 Development Scenario Groups (90 queries).

 |

Your pipeline is moving forward. Run `build_retrieval_indices.py` on your machine, then open `data/eboss_corpus_chunks_v1.json` to begin writing the first scenario groups for Task T05.