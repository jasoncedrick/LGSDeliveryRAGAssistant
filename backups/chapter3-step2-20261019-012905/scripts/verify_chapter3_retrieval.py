"""Read-only corpus/index audit. Does not load or run any benchmark queries.

From the repository root:
    python -B scripts/verify_chapter3_retrieval.py
Exit 1 means the existing artifacts need review, not permission to overwrite them.
"""
import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.chunk_retriever import audit_chunk_tokens, MODEL_NAME


def main():
    import faiss
    from transformers import AutoTokenizer

    chunks = json.loads((ROOT/'data/eboss_corpus_chunks_v1.json').read_text(encoding='utf-8'))
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, local_files_only=True)
    report = audit_chunk_tokens(chunks, tokenizer)
    with (ROOT/'data/bm25_index.pkl').open('rb') as handle:
        bundle = pickle.load(handle)
    index = faiss.read_index(str(ROOT/'data/faiss_index.bin'))
    report.update(
        bm25_content_and_order_match=bundle.get('chunks') == chunks,
        bm25_row_count=bundle['bm25'].corpus_size,
        faiss_row_count=index.ntotal, faiss_dimension=index.d,
        faiss_inner_product=index.metric_type == faiss.METRIC_INNER_PRODUCT,
        unique_chunk_ids=len({c['chunk_id'] for c in chunks}) == len(chunks),
        held_out_benchmarks_accessed=False,
        note='Row counts do not independently prove FAISS vector-to-text provenance.')
    report['passed'] = bool(
        report['passes_text_length_validation'] and report['bm25_content_and_order_match']
        and report['unique_chunk_ids'] and report['faiss_inner_product']
        and index.d == 384 and index.ntotal == len(chunks) == bundle['bm25'].corpus_size)
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
