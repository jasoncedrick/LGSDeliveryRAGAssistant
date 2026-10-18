"""Chapter 3.2.4 chunk scoring, separate from the experimental section runtime.

Uses the existing frozen manifest's weights, without tuning or benchmark reads.
Factory loading verifies source token windows when present, or audits legacy text.
No section expansion, office routing, or answer validation is performed here.
"""
from __future__ import annotations

import hashlib
import json
import pickle
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODEL_NAME = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'


def min_max_normalize(values):
    values = np.asarray(values, dtype=float)
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all():
        raise ValueError('Scores must be a nonempty finite vector')
    span = values.max() - values.min()
    return (values - values.min()) / span if span else np.zeros_like(values)


def audit_chunk_tokens(chunks, tokenizer):
    """Read-only recount of serialized text; overlap here is diagnostic only.

    Decoding/re-encoding subword windows can change boundary tokens. An overlap
    mismatch in serialized text does not prove the original splitter used the
    wrong stride. Original token offsets are needed for that separate check.
    """
    over_limit, count_mismatches, overlap_mismatches = [], [], []
    actual_max, pairs = 0, 0
    previous_by_page = {}
    for chunk in chunks:
        ids = tokenizer.encode(chunk['text_content'], add_special_tokens=False)
        actual_max = max(actual_max, len(ids))
        detail = {'chunk_id': chunk['chunk_id'],
                  'stored_tokens': chunk.get('token_count'), 'actual_tokens': len(ids)}
        if not ids or len(ids) > 120:
            over_limit.append(detail)
        if chunk.get('token_count') != len(ids):
            count_mismatches.append(detail)
        key = (chunk['file_source'], chunk.get('pdf_relative_page'))
        if key in previous_by_page:
            previous_id, previous_tokens = previous_by_page[key]
            pairs += 1
            if previous_tokens[-20:] != ids[:20]:
                overlap_mismatches.append([previous_id, chunk['chunk_id']])
        previous_by_page[key] = (chunk['chunk_id'], ids)
    return {'chunk_count': len(chunks), 'actual_max_tokens': actual_max,
            'invalid_length_count': len(over_limit), 'invalid_lengths': over_limit,
            'stored_count_mismatch_count': len(count_mismatches),
            'stored_count_mismatches': count_mismatches,
            'adjacent_page_pairs': pairs,
            'retokenized_overlap_mismatch_count': len(overlap_mismatches),
            'retokenized_overlap_mismatches': overlap_mismatches,
            'overlap_note': 'Diagnostic only; verify source token windows before rebuilding.',
            'passes_text_length_validation': bool(chunks) and not over_limit and not count_mismatches}


class ChunkRetriever:
    """Score each chunk over the full corpus, then select K=3 or K=5.

    Constructor accepts injected components for deterministic offline tests.
    Application callers should use from_files() to validate artifact inputs.
    """

    def __init__(self, chunks, dictionary, bm25, faiss_index, embedder, manifest):
        settings = manifest['constraints']
        if settings.get('chunk_tokens') != 120 or settings.get('overlap_tokens') != 20:
            raise ValueError('Chapter 3 requires a 120-token window and 20-token overlap')
        self.top_k = manifest['optimal_top_k']
        if type(self.top_k) is not int or self.top_k not in (3, 5):
            raise ValueError('Chapter 3 Top-K must be 3 or 5')
        weights = manifest['optimal_retrieval_weights']
        self.weights = np.asarray([weights['alpha_bm25'], weights['beta_dense'],
                                   weights['gamma_dict']], dtype=float)
        if (not np.isfinite(self.weights).all() or (self.weights < 0).any()
                or not np.isclose(self.weights.sum(), 1, rtol=0, atol=1e-9)):
            raise ValueError('Fusion weights must be nonnegative and sum to one')
        if not chunks or len({c['chunk_id'] for c in chunks}) != len(chunks):
            raise ValueError('Corpus must contain unique chunk IDs')
        if len(chunks) < self.top_k:
            raise ValueError('Corpus contains fewer than K chunks')
        if bm25.corpus_size != len(chunks) or faiss_index.ntotal != len(chunks):
            raise ValueError('Corpus and index row counts do not match')
        self.chunks = chunks
        self.terms = [term.lower() for term in dictionary]
        self.texts_lower = [chunk['text_content'].lower() for chunk in chunks]
        self.bm25, self.index, self.embedder = bm25, faiss_index, embedder
        self.artifact_hashes = {}

    @classmethod
    def from_files(cls, *, corpus_path=ROOT/'data/eboss_corpus_chunks_v1.json',
                   dictionary_path=ROOT/'data/municipal_dictionary_v1.json',
                   bm25_path=ROOT/'data/bm25_index.pkl',
                   faiss_path=ROOT/'data/faiss_index.bin',
                   manifest_path=ROOT/'config/pipeline_manifest.json'):
        """Load trusted local artifacts once; never download, rebuild, or tune."""
        import faiss
        from transformers import AutoTokenizer
        from sentence_transformers import SentenceTransformer

        paths = {name: Path(path) for name, path in {
            'corpus': corpus_path, 'dictionary': dictionary_path, 'bm25': bm25_path,
            'faiss': faiss_path, 'manifest': manifest_path}.items()}
        chunks = json.loads(paths['corpus'].read_text(encoding='utf-8-sig'))
        manifest = json.loads(paths['manifest'].read_text(encoding='utf-8-sig'))
        if manifest['models']['embedder'] != MODEL_NAME:
            raise ValueError('Unexpected embedder for this Chapter 3 implementation')
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, local_files_only=True)
        if any('embedding_input_ids' in chunk for chunk in chunks):
            from src.token_windows import verify_source_windows

            paths['source_pages'] = paths['corpus'].parent/'source_pages.json'
            paths['provenance'] = paths['corpus'].parent/'index_provenance.json'
            provenance = json.loads(paths['provenance'].read_text(encoding='utf-8'))
            if (provenance.get('embedding_path') != 'source_token_ids'
                    or provenance.get('model') != MODEL_NAME):
                raise ValueError('Unexpected index embedding provenance')
            for name in ('corpus', 'source_pages', 'bm25', 'faiss', 'manifest'):
                path = paths[name]
                if provenance['files'].get(path.name) != hashlib.sha256(path.read_bytes()).hexdigest():
                    raise ValueError(f'Artifact provenance mismatch: {name}')
            pages = json.loads(paths['source_pages'].read_text(encoding='utf-8'))
            verify_source_windows(chunks, pages, tokenizer)
        else:
            audit = audit_chunk_tokens(chunks, tokenizer)
            if not audit['passes_text_length_validation']:
                raise ValueError(
                    'Corpus text fails Chapter 3 token validation: '
                    f"{audit['invalid_length_count']} invalid lengths; "
                    f"{audit['stored_count_mismatch_count']} stale token counts. "
                    'Run scripts/verify_chapter3_retrieval.py for the read-only audit. '
                    'Preserve frozen artifacts; prepare a separate development corpus.')
        # Pickle is used only for the project's trusted, locally built BM25 file.
        with paths['bm25'].open('rb') as handle:
            bundle = pickle.load(handle)
        if bundle.get('chunks') != chunks:
            raise ValueError('BM25 chunk content/order differs from the supplied corpus')
        index = faiss.read_index(str(paths['faiss']))
        if index.d != 384 or index.metric_type != faiss.METRIC_INNER_PRODUCT:
            raise ValueError('Expected a 384-dimensional inner-product FAISS index')
        # Resolve the cached snapshot first, avoiding network access in model init.
        from huggingface_hub import snapshot_download
        snapshot = snapshot_download(MODEL_NAME, local_files_only=True)
        embedder = SentenceTransformer(snapshot, device='cpu')
        retriever = cls(chunks,
                        json.loads(paths['dictionary'].read_text(encoding='utf-8-sig')),
                        bundle['bm25'], index, embedder, manifest)
        retriever.artifact_hashes = {
            name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()}
        return retriever

    def retrieve(self, normalized_query, *, top_k=None):
        if not isinstance(normalized_query, str) or not normalized_query.strip():
            raise ValueError('A nonempty normalized query is required')
        k = self.top_k if top_k is None else top_k
        if type(k) is not int or k not in (3, 5) or k > len(self.chunks):
            raise ValueError('Top-K must be 3 or 5 and fit the corpus')
        query = normalized_query.strip()
        count = len(self.chunks)
        sparse = np.asarray(self.bm25.get_scores(query.lower().split()), dtype=float)
        if sparse.shape != (count,):
            raise ValueError('BM25 did not return one score per chunk')
        embeddings = np.asarray(self.embedder.encode([query], normalize_embeddings=True),
                                dtype=np.float32)
        if embeddings.shape != (1, self.index.d) or not np.isfinite(embeddings).all():
            raise ValueError('Invalid query embedding')
        distances, indices = self.index.search(embeddings, count)
        if (indices.shape != (1, count) or distances.shape != (1, count)
                or sorted(indices[0].tolist()) != list(range(count))):
            raise ValueError('FAISS must return each corpus row exactly once')
        dense = np.empty(count, dtype=float)
        dense[indices[0]] = distances[0]
        # Keep the recorded evaluation's substring matching convention unchanged.
        matched_terms = [term for term in self.terms if term in query.lower()]
        boost = np.asarray([sum(term in text for term in matched_terms)
                            for text in self.texts_lower], dtype=float)
        raw = np.column_stack([sparse, dense, boost])
        normalized = np.column_stack([min_max_normalize(raw[:, i]) for i in range(3)])
        fused = normalized @ self.weights
        # Stable corpus-order tie breaking makes repeated calls reproducible.
        selected = np.argsort(-fused, kind='stable')[:k]
        ranked, citations, blocks = [], [], []
        for rank, idx in enumerate(selected, 1):
            chunk = self.chunks[int(idx)]
            label = f'S{rank}'
            ranked.append({'rank': rank, 'chunk_id': chunk['chunk_id'],
                           'final_score': float(fused[idx]),
                           'raw_scores': dict(zip(('bm25', 'dense', 'dictionary'),
                                                  map(float, raw[idx]))),
                           'normalized_scores': dict(zip(('bm25', 'dense', 'dictionary'),
                                                         map(float, normalized[idx])))})
            citations.append({'citation': label, 'chunk_id': chunk['chunk_id'],
                              'file_source': chunk['file_source'],
                              'source_page': chunk.get('source_page'),
                              'pdf_relative_page': chunk.get('pdf_relative_page'),
                              'text': chunk['text_content']})
            blocks.append(f"[{label}] {chunk['file_source']} | printed page "
                          f"{chunk.get('source_page')} | chunk {chunk['chunk_id']}\n"
                          f"{chunk['text_content']}")
        return {'status': 'CONTEXT_READY', 'retrieval_mode': 'chapter3_chunks',
                'top_k': k, 'candidate_count': count,
                'weights': dict(zip(('alpha_bm25', 'beta_dense', 'gamma_dict'),
                                    map(float, self.weights))),
                'matched_dictionary_terms': matched_terms, 'ranked_chunks': ranked,
                'source_chunk_ids': [r['chunk_id'] for r in ranked],
                'citations': citations, 'context': '\n\n'.join(blocks),
                'artifact_hashes': dict(self.artifact_hashes)}
