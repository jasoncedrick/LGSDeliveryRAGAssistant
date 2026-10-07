"""
Pipeline singleton for the FastAPI backend (Thesis Sec 3.2.6: Deploy the Web
Application). Loads all models and indices ONCE at application startup and
exposes handle_query() for the API to call per request.

Reuses the exact same normalization + hybrid retrieval + generation logic
as scripts/chat_cli.py and scripts/run_test_comparison.py, just packaged as
a class so a long-lived server process can hold everything in memory
instead of a one-shot script re-loading it every run. Per Sec 3.2.6: "The
pre-built BM25 and FAISS indices are loaded into server memory at
application startup as offline artifacts, guaranteeing that index loading
is a one-time cost and does not contribute to per-query response latency."
"""

import os
import json
import pickle
import numpy as np
import requests
from sentence_transformers import SentenceTransformer
import faiss

from src.query_normalizer import QueryNormalizer

CORPUS_PATH = "data/eboss_corpus_chunks_v1.json"
DICT_PATH = "data/municipal_dictionary_v1.json"
FAISS_INDEX_PATH = "data/faiss_index.bin"
BM25_INDEX_PATH = "data/bm25_index.pkl"
MANIFEST_PATH = "config/pipeline_manifest.json"

# Configurable via env var so the backend can point at Ollama running
# elsewhere (e.g. tunneled from your own machine) without a code change --
# see the deployment note on free-tier hosting and local-model constraints.
OLLAMA_ENDPOINT = os.environ.get("OLLAMA_ENDPOINT", "http://localhost:11434/api/generate")
MODEL_NAME = os.environ.get("EBOSS_MODEL_NAME", "eboss-mistral")
EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Per Sec 3.2.5 "Prompt Engineering and Response Structure": hardcoded
# fallback instruction when retrieved context is insufficient, in Bisaya,
# plus Sec 3.2.5 "Response Language Matching": respond in the citizen's
# original dialect/language style.
ANSWER_SYSTEM_PROMPT = """You are eBOSS, a helpful assistant for Davao City government services.
Answer the citizen's question using ONLY the information in the provided context chunks from the Davao City Citizens' Charter.
Rules:
1. If the context does not contain the answer, respond EXACTLY: "Wala akoy nakit-an nga impormasyon bahin niini sa Citizens' Charter."
2. Be concise and clear.
3. Name the responsible office when the context states it.
4. Do not invent fees, requirements, deadlines, or procedures that are not in the context.
5. Respond in the same dialect/language style as the citizen's original query.
"""

FALLBACK_ANSWER = "Wala akoy nakit-an nga impormasyon bahin niini sa Citizens' Charter."


def min_max_normalize(scores: np.ndarray) -> np.ndarray:
    min_v = np.min(scores)
    max_v = np.max(scores)
    if max_v - min_v < 1e-8:
        return np.zeros_like(scores)
    return (scores - min_v) / (max_v - min_v + 1e-8)


def load_normalized_dictionary(path: str) -> list:
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    entries = []
    for term, fields in raw.items():
        entry = dict(fields)
        entry.setdefault("local_term", term)
        entries.append(entry)
    return entries


class Pipeline:
    def __init__(self, warmup: bool = True):
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        weights = manifest["optimal_retrieval_weights"]
        self.alpha = weights["alpha_bm25"]
        self.beta = weights["beta_dense"]
        self.gamma = weights["gamma_dict"]
        self.top_k = manifest["optimal_top_k"]

        with open(CORPUS_PATH, "r", encoding="utf-8") as f:
            self.corpus = json.load(f)
        self.chunk_ids = [c["chunk_id"] for c in self.corpus]
        self.chunk_texts = [c["text_content"] for c in self.corpus]
        self.chunk_by_id = {c["chunk_id"]: c for c in self.corpus}

        self.dictionary = load_normalized_dictionary(DICT_PATH)

        with open(BM25_INDEX_PATH, "rb") as f:
            self.bm25 = pickle.load(f)["bm25"]
        self.faiss_index = faiss.read_index(FAISS_INDEX_PATH)
        self.embedder = SentenceTransformer(EMBED_MODEL_NAME, device="cpu")
        self.normalizer = QueryNormalizer(DICT_PATH)

        if warmup:
            # First Ollama call loads the model into VRAM (10-30s); do it
            # once at startup, not on the first citizen's request.
            self.normalizer.normalize("Unsaon pagkuha ug permit?")

    def _score_bm25(self, text: str) -> np.ndarray:
        tokens = text.lower().split()
        return np.array(self.bm25.get_scores(tokens))

    def _score_dense(self, text: str) -> np.ndarray:
        emb = self.embedder.encode([text], normalize_embeddings=True)
        dense = np.zeros(len(self.corpus))
        D, I = self.faiss_index.search(emb.astype(np.float32), len(self.corpus))
        for rank, idx in enumerate(I[0]):
            dense[idx] = D[0][rank]
        return dense

    def _score_dict_boost(self, text: str) -> np.ndarray:
        matched = [t["local_term"].lower() for t in self.dictionary if t["local_term"].lower() in text.lower()]
        boost = np.zeros(len(self.corpus))
        if matched:
            for idx, ctext in enumerate(self.chunk_texts):
                ctext_lower = ctext.lower()
                boost[idx] = sum(1 for kw in matched if kw in ctext_lower)
        return boost

    def _retrieve_topk(self, normalized_query: str) -> list:
        bm25_raw = self._score_bm25(normalized_query)
        dense_raw = self._score_dense(normalized_query)
        boost_raw = self._score_dict_boost(normalized_query)
        bm25_n = min_max_normalize(bm25_raw)
        dense_n = min_max_normalize(dense_raw)
        boost_n = min_max_normalize(boost_raw)
        fused = self.alpha * bm25_n + self.beta * dense_n + self.gamma * boost_n
        top_idx = np.argsort(-fused)[: self.top_k]
        return [self.chunk_ids[i] for i in top_idx]

    def _generate_answer(self, raw_query: str, context_chunks: list) -> dict:
        context_text = "\n\n".join(
            f"[{c['chunk_id']} | {c.get('pillar', 'N/A')}]\n{c['text_content']}"
            for c in context_chunks
        )
        prompt = f"""{ANSWER_SYSTEM_PROMPT}

Context:
{context_text}

Citizen Question: {raw_query}
Answer:"""
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.0, "top_p": 0.0, "num_predict": 400},
        }
        try:
            res = requests.post(OLLAMA_ENDPOINT, json=payload, timeout=120)
            res.raise_for_status()
            result = res.json()
            return {"answer": result.get("response", "").strip(), "tokens_generated": result.get("eval_count", 0)}
        except requests.exceptions.RequestException as e:
            return {"answer": FALLBACK_ANSWER, "tokens_generated": 0, "error": str(e)}

    def handle_query(self, raw_query: str) -> dict:
        """Runs one citizen query through the full pipeline sequence from
        Sec 3.2.6: dictionary lookup + lexical injection -> LLM-based query
        normalization -> hybrid BM25+FAISS retrieval with weighted fusion ->
        prompt construction -> grounded LLM response generation."""
        norm_result = self.normalizer.normalize(raw_query)
        normalized_query = norm_result["normalized_query"] or raw_query

        retrieved_ids = self._retrieve_topk(normalized_query)
        context_chunks = [self.chunk_by_id[cid] for cid in retrieved_ids]
        gen_result = self._generate_answer(raw_query, context_chunks)
        
        return {
            "raw_query": raw_query,
            "normalized_query": normalized_query,
            "normalization_status": norm_result["status"],
            "clarification_prompt": norm_result["clarification_prompt"],
            "injected_terms": norm_result["injected_terms"],
            "retrieved_chunk_ids": retrieved_ids,
            "retrieved_chunks": [
                {"chunk_id": c["chunk_id"], "pillar": c.get("pillar"), "text_content": c["text_content"]}
                for c in context_chunks
            ],
            "answer": gen_result["answer"],
            "tokens_generated": gen_result["tokens_generated"],
        }