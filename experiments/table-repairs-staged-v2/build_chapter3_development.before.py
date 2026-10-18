"""Build a separate 120/20 development corpus and paired indices; no benchmark reads.

Run from the project root with the existing venv. A fresh output directory is
required so previous artifacts cannot be overwritten accidentally.
"""
import argparse
import hashlib
import json
import pickle
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.chunk_retriever import MODEL_NAME
from src.token_windows import source_windows, verify_source_windows, embed_source_windows
from scripts.ingest_eboss_corpus import INGESTION_CATALOG


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def extract_page(page):
    # Keep Unicode, numbers, units, negation, and table block order. No LLM repair.
    text = '\n'.join(b[4].strip() for b in page.get_text('blocks') if b[4].strip())
    text = text.replace('\r\n', '\n').strip()
    lines = text.splitlines()
    printed_page = None
    # Remove only a standalone leading/trailing printed page number, not body rows.
    if lines and re.fullmatch(r'\d{1,4}', lines[0].strip()):
        printed_page = int(lines.pop(0).strip())
    elif lines and re.fullmatch(r'\d{1,4}', lines[-1].strip()):
        printed_page = int(lines.pop().strip())
    return '\n'.join(lines).strip(), printed_page


def build(output):
    import faiss
    import fitz
    import numpy as np
    import torch
    from rank_bm25 import BM25Okapi
    from sentence_transformers import SentenceTransformer
    from transformers import AutoTokenizer
    from huggingface_hub import snapshot_download

    output = Path(output).resolve()
    if output == ROOT or ROOT not in output.parents or 'experiments' not in output.relative_to(ROOT).parts:
        raise ValueError('Output must be a new experiments subdirectory in this repository')
    if output.exists():
        raise FileExistsError('Use a fresh output directory; existing artifacts are preserved')
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, local_files_only=True)
    chunks, pages, sources, text_issues = [], [], [], []
    for entry in INGESTION_CATALOG:
        pdf = ROOT/'data/raw_charters'/entry['file_name']
        sha = digest(pdf)
        with fitz.open(pdf) as document:
            sources.append({'file_source': pdf.name, 'sha256': sha, 'pdf_pages': len(document)})
            for page in document:
                text, printed = extract_page(page)
                if not text:
                    text_issues.append({'file_source': pdf.name, 'pdf_relative_page': page.number+1,
                                        'issue': 'No extracted text; review for scanned/blank page'})
                    continue
                page_id = f"{entry['pillar_code']}-PDF{page.number+1:04d}"
                provenance = {'source_page_id': page_id, 'file_source': pdf.name,
                              'pdf_relative_page': page.number+1, 'source_page': printed,
                              'pdf_sha256': sha}
                pages.append({**provenance, 'text': text,
                              'text_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()})
                if '\ufffd' in text:
                    text_issues.append({**provenance, 'issue': 'Replacement character in PDF extraction'})
                for i, window in enumerate(source_windows(text, tokenizer), 1):
                    chunks.append({**provenance, **window,
                                   'chunk_id': f'DEV120-{page_id}-C{i:03d}',
                                   'governance_pillar': entry['pillar'],
                                   'document_title': entry['document_title'],
                                   'version_date': '2022' if entry['pillar_code'] == 'BFP' else '2026',
                                   'corpus_version': 'chapter3-source-token-windows-dev'})
    if len({c['chunk_id'] for c in chunks}) != len(chunks):
        raise ValueError('Duplicate development chunk IDs')
    audit = verify_source_windows(chunks, pages, tokenizer)
    print(f"Verified {len(chunks)} chunks; {audit['verified_overlap_pairs']} exact 20-token overlaps.", flush=True)
    snapshot = snapshot_download(MODEL_NAME, local_files_only=True)
    torch.set_num_threads(4)
    model = SentenceTransformer(snapshot, device='cpu')
    # Check that direct-token forwarding agrees with encode() on intact short text.
    probe = 'Application for a business permit.'
    probe_ids = model.tokenizer.encode(probe, add_special_tokens=False)
    direct = embed_source_windows([{'embedding_input_ids': probe_ids}], model)
    regular = model.encode([probe], normalize_embeddings=True)
    if not np.allclose(direct, regular, atol=1e-6):
        raise ValueError('Direct-token embedding disagrees with SentenceTransformer.encode')
    print('Embedding original token windows with cached MiniLM on CPU...', flush=True)
    vectors = embed_source_windows(chunks, model)
    bm25 = BM25Okapi([c['text_content'].lower().split() for c in chunks])
    index = faiss.IndexFlatIP(384)
    index.add(vectors)
    if not np.array_equal(index.reconstruct_n(0, len(chunks)), vectors):
        raise ValueError('FAISS row order/vector mismatch')
    output.mkdir(parents=True, exist_ok=False)
    write_json(output/'corpus.json', chunks)
    write_json(output/'source_pages.json', pages)
    with (output/'bm25_index.pkl').open('wb') as handle:
        pickle.dump({'bm25': bm25, 'chunks': chunks}, handle)
    faiss.write_index(index, str(output/'faiss_index.bin'))
    saved = faiss.read_index(str(output/'faiss_index.bin'))
    if not np.array_equal(saved.reconstruct_n(0, len(chunks)), vectors):
        raise ValueError('Saved FAISS vectors differ from built vectors')
    audit.update(text_extraction_review_items=text_issues, source_pdfs=sources,
                 embedding_dimension=384, faiss_rows=index.ntotal, bm25_rows=bm25.corpus_size,
                 direct_embedding_matches_encode=True, serialized_faiss_vectors_verified=True,
                 benchmark_accessed=False,
                 source_layout_review_complete=False,
                 note='Technical token/index validation only; table fidelity still requires source-page review.')
    write_json(output/'validation.json', audit)
    # Preserve recorded weights, but do not mislabel this newly built corpus as frozen.
    manifest = json.loads((ROOT/'config/pipeline_manifest.json').read_text(encoding='utf-8'))
    manifest['status'] = 'development_not_frozen'
    manifest['task_origin'] = 'Chapter3 Step2 source-token-window development build'
    manifest['prior_development_metrics_not_revalidated'] = manifest.pop('retrieval_metrics_dev', {})
    manifest['corpus_artifacts'] = {'corpus': 'corpus.json', 'source_pages': 'source_pages.json',
                                  'bm25': 'bm25_index.pkl', 'faiss': 'faiss_index.bin'}
    write_json(output/'pipeline_manifest.json', manifest)
    write_json(output/'index_provenance.json', {
        'status': 'development_not_frozen', 'model': MODEL_NAME,
        'model_snapshot': Path(snapshot).name,
        'embedding_path': 'source_token_ids', 'window_tokens': 120, 'overlap_tokens': 20,
        'dimension': 384, 'row_count': len(chunks),
        'files': {name: digest(output/name) for name in
                  ('corpus.json', 'source_pages.json', 'bm25_index.pkl', 'faiss_index.bin',
                   'pipeline_manifest.json', 'validation.json')},
        'source_pdfs': sources,
        'build_code_sha256': {str(p.relative_to(ROOT)): digest(p) for p in
                             (Path(__file__), ROOT/'src/token_windows.py')},
        'held_out_benchmarks_accessed': False})
    print(f'Created separate development artifacts: {output}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, help='New experiments subdirectory')
    build(parser.parse_args().output)
