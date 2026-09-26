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