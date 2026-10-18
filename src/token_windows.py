"""Lossless token-window provenance and direct MiniLM embedding for Chapter 3.

Window size is 120 source tokens, stride is 100, overlap is 20. Only the final
window of a page may be shorter. Display text uses original character offsets;
it is never decoded and re-tokenized to produce the document embedding.
"""
from __future__ import annotations

import hashlib

WINDOW = 120
OVERLAP = 20
STRIDE = WINDOW - OVERLAP


def prepare_window_ids(ids, tokenizer):
    """Add MiniLM's XLM-R start/end tokens explicitly.

    The cached generic PreTrainedTokenizerFast's Python build_inputs method is a
    no-op; its Rust text encoder adds these tokens. Verify parity before embedding.
    """
    if tokenizer.cls_token_id is None or tokenizer.sep_token_id is None:
        raise ValueError('Expected XLM-R start/end special tokens')
    return [tokenizer.cls_token_id, *ids, tokenizer.sep_token_id]


def source_windows(text, tokenizer):
    encoded = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)
    tokens, offsets = encoded['input_ids'], encoded['offset_mapping']
    for start in range(0, len(tokens), STRIDE):
        end = min(start + WINDOW, len(tokens))
        char_start, char_end = offsets[start][0], offsets[end - 1][1]
        yield {'token_start': start, 'token_end': end,
               'char_start': char_start, 'char_end': char_end,
               'embedding_input_ids': tokens[start:end], 'token_count': end-start,
               'text_content': text[char_start:char_end]}
        if end == len(tokens):
            break


def verify_source_windows(chunks, source_pages, tokenizer):
    """Reconstruct every window from its stored source page, in source order."""
    pages = {p['source_page_id']: p for p in source_pages}
    if len(pages) != len(source_pages):
        raise ValueError('Duplicate source page IDs')
    grouped = {}
    for chunk in chunks:
        grouped.setdefault(chunk['source_page_id'], []).append(chunk)
    if set(grouped) != set(pages):
        raise ValueError('Source pages and chunk page references differ')
    pairs = 0
    max_input = 0
    retokenized_over = 0
    for page_id, page in pages.items():
        if hashlib.sha256(page['text'].encode('utf-8')).hexdigest() != page['text_sha256']:
            raise ValueError(f'Source text hash mismatch: {page_id}')
        expected = list(source_windows(page['text'], tokenizer))
        actual = grouped[page_id]
        if len(expected) != len(actual):
            raise ValueError(f'Missing or extra source windows: {page_id}')
        for i, (want, got) in enumerate(zip(expected, actual)):
            if any(got.get(key) != value for key, value in want.items()):
                raise ValueError(f'Token IDs, offsets or source text differ: {got["chunk_id"]}')
            for key in ('file_source', 'pdf_relative_page', 'source_page', 'pdf_sha256'):
                if got.get(key) != page.get(key):
                    raise ValueError(f'Source metadata differs: {got["chunk_id"]}: {key}')
            if not 0 < len(got['embedding_input_ids']) <= WINDOW:
                raise ValueError('Empty or over-limit token window')
            prepared = prepare_window_ids(got['embedding_input_ids'], tokenizer)
            max_input = max(max_input, len(prepared))
            retokenized_over += len(tokenizer.encode(got['text_content'], add_special_tokens=False)) > WINDOW
            if i:
                if actual[i-1]['embedding_input_ids'][-OVERLAP:] != got['embedding_input_ids'][:OVERLAP]:
                    raise ValueError('Source token overlap is not exactly 20')
                pairs += 1
    if max_input > 128:
        raise ValueError('MiniLM sequence limit exceeded including special tokens')
    return {'passed': bool(chunks), 'chunk_count': len(chunks), 'source_page_count': len(pages),
            'window_tokens': WINDOW, 'stride_tokens': STRIDE, 'overlap_tokens': OVERLAP,
            'verified_overlap_pairs': pairs, 'max_embedding_input_tokens': max_input,
            'display_text_retokenized_over_120': retokenized_over,
            'embedding_path': 'verified source token IDs; display text is not re-tokenized'}


def embed_source_windows(chunks, model, batch_size=32):
    """Use the same transformer/pooling/normalization as encode(), without a text round trip."""
    import numpy as np
    import torch

    model.eval()
    probe = 'Application for a business permit.'
    if prepare_window_ids(model.tokenizer.encode(probe, add_special_tokens=False), model.tokenizer) != model.tokenizer.encode(probe):
        raise ValueError('Special-token preparation differs from the model tokenizer')
    arrays = []
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start:start+batch_size]
        ids = [prepare_window_ids(c['embedding_input_ids'], model.tokenizer) for c in batch]
        if any(not 0 < len(c['embedding_input_ids']) <= WINDOW for c in batch):
            raise ValueError('Invalid document token window')
        if max(map(len, ids)) > min(128, model.max_seq_length):
            raise ValueError('Document sequence would exceed model limit')
        features = model.tokenizer.pad({'input_ids': ids}, padding=True, return_tensors='pt')
        features = {key: value.to(model.device) for key, value in features.items()}
        with torch.inference_mode():
            vectors = model(features)['sentence_embedding']
            vectors = torch.nn.functional.normalize(vectors, p=2, dim=1)
        arrays.append(vectors.cpu().numpy())
    if not arrays:
        raise ValueError('No document windows to embed')
    result = np.vstack(arrays).astype(np.float32)
    if result.shape != (len(chunks), 384) or not np.isfinite(result).all():
        raise ValueError('Invalid MiniLM embeddings')
    return result
