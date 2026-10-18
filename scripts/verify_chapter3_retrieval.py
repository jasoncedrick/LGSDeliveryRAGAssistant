"""Read-only corpus/index audit. Does not load or run any benchmark queries.

From the repository root:
    python -B scripts/verify_chapter3_retrieval.py
Exit 1 means the existing artifacts need review, not permission to overwrite them.
"""
import argparse
import hashlib
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

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts', type=Path, help='Separate development artifact directory')
    args = parser.parse_args()
    directory = args.artifacts.resolve() if args.artifacts else ROOT/'data'
    corpus_path = directory/('corpus.json' if args.artifacts else 'eboss_corpus_chunks_v1.json')
    chunks = json.loads(corpus_path.read_text(encoding='utf-8'))
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, local_files_only=True)
    if args.artifacts:
        from src.token_windows import verify_source_windows

        pages = json.loads((directory/'source_pages.json').read_text(encoding='utf-8'))
        report = verify_source_windows(chunks, pages, tokenizer)
        provenance = json.loads((directory/'index_provenance.json').read_text(encoding='utf-8'))
        report['artifact_hashes_match'] = all(
            hashlib.sha256((directory/name).read_bytes()).hexdigest() == sha
            for name, sha in provenance['files'].items())
        report['source_pdf_hashes_match'] = all(
            hashlib.sha256((ROOT/'data/raw_charters'/source['file_source']).read_bytes()).hexdigest() == source['sha256']
            for source in provenance['source_pdfs'])
        token_valid = report['passed'] and report['artifact_hashes_match'] and report['source_pdf_hashes_match']
    else:
        report = audit_chunk_tokens(chunks, tokenizer)
        token_valid = report['passes_text_length_validation']
    with (directory/'bm25_index.pkl').open('rb') as handle:
        bundle = pickle.load(handle)
    index = faiss.read_index(str(directory/'faiss_index.bin'))
    report.update(
        bm25_content_and_order_match=bundle.get('chunks') == chunks,
        bm25_row_count=bundle['bm25'].corpus_size,
        faiss_row_count=index.ntotal, faiss_dimension=index.d,
        faiss_inner_product=index.metric_type == faiss.METRIC_INNER_PRODUCT,
        unique_chunk_ids=len({c['chunk_id'] for c in chunks}) == len(chunks),
        held_out_benchmarks_accessed=False,
        note='Row counts do not independently prove FAISS vector-to-text provenance.')
    report['passed'] = bool(
        token_valid and report['bm25_content_and_order_match']
        and report['unique_chunk_ids'] and report['faiss_inner_product']
        and index.d == 384 and index.ntotal == len(chunks) == bundle['bm25'].corpus_size)
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
