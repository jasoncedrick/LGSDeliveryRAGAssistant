"""Source-only ID crosswalk; no query/answer matching and no benchmark edits."""
import hashlib
import json
from pathlib import Path
import re
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'experiments/t07-final-evaluation-v1'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def indexed_identity(text):
    chars, positions = [], []
    for position, char in enumerate(text):
        for normalized in unicodedata.normalize('NFKD', char).casefold():
            if normalized.isalnum():
                chars.append(normalized)
                positions.append(position)
    return ''.join(chars), positions


def numbers(text):
    return re.findall(r'\d+(?:[.,]\d+)*%?', text)


def locate_span(legacy, page):
    text = re.sub(r'^' + re.escape(str(legacy['source_page'])) + r'\s+', '', legacy['text_content'])
    needle, _ = indexed_identity(text)
    haystack, offsets = indexed_identity(page['text'])
    start = haystack.find(needle) if needle else -1
    if start < 0:
        return None, 'NO_FULL_SOURCE_IDENTITY'
    if haystack.find(needle, start + 1) >= 0:
        return None, 'AMBIGUOUS_SOURCE_OCCURRENCE'
    lo, hi = offsets[start], offsets[start + len(needle) - 1] + 1
    if numbers(text) != numbers(page['text'][lo:hi]):
        return None, 'NUMERIC_SIGNATURE_MISMATCH'
    return (lo, hi), None


def main():
    reg = read(OUT / 'candidate_registration.json')
    assert sha(OUT / 'candidate_registration.json') == read(OUT / 'registration_seal.json')['candidate_registration_sha256']
    assert all(sha(ROOT / name) == value for name, value in reg['file_hashes'].items())
    target = OUT / 'source_span_crosswalk.json'
    assert not target.exists(), 'Preserve registered mapping; use an explicit new version.'
    benchmark = Path(reg['held_out_path'])
    groups = read(benchmark)
    legacy_path = Path('D:/thesis/LGSDeliveryRAGAssistant-main/data/eboss_corpus_chunks_v1.json')
    legacy = {c['chunk_id']: c for c in read(legacy_path)}
    base = ROOT / 'experiments/chapter3-table-repaired-development-v1'
    corpus = read(base / 'corpus.json')
    pages = {(p['file_source'], p['pdf_relative_page']): p for p in read(base / 'source_pages.json')}
    mappings = {}
    for cid in sorted({cid for g in groups for cid in g['ground_truth_chunk_ids']}):
        old = legacy.get(cid)
        item = dict(legacy_id=cid, mapped_ids=[], status='UNRESOLVED')
        mappings[cid] = item
        if old is None:
            item['reason'] = 'LEGACY_ID_MISSING'
            continue
        page = pages.get((old['file_source'], old['pdf_relative_page']))
        if page is None:
            item['reason'] = 'SOURCE_PAGE_MISSING'
            continue
        span, error = locate_span(old, page)
        if error:
            item['reason'] = error
            continue
        lo, hi = span
        overlapping = [c for c in corpus if c['source_page_id'] == page['source_page_id']
            and c['char_start'] < hi and c['char_end'] > lo
            and indexed_identity(page['text'][max(lo, c['char_start']):min(hi, c['char_end'])])[0]]
        # Every alphanumeric source character in the original annotation must
        # be covered by the transferred chunk windows; no page-wide assignment.
        relevant_positions = [i for i in range(lo, hi) if page['text'][i].isalnum()]
        covered = all(any(c['char_start'] <= i < c['char_end'] for c in overlapping) for i in relevant_positions)
        if not covered or not overlapping:
            item['reason'] = 'SOURCE_SPAN_WINDOW_COVERAGE_GAP'
            continue
        item.update(status='SOURCE_SPAN_TRANSFERRED', source_page_id=page['source_page_id'],
            source_char_start=lo, source_char_end=hi, mapped_ids=[c['chunk_id'] for c in overlapping],
            numeric_signature_verified=True, source_text_sha256=hashlib.sha256(page['text'][lo:hi].encode()).hexdigest(),
            window_intersections=[dict(chunk_id=c['chunk_id'], start=max(lo, c['char_start']), end=min(hi, c['char_end'])) for c in overlapping])
    group_map = {}
    for group in groups:
        unresolved = [cid for cid in group['ground_truth_chunk_ids'] if not mappings[cid]['mapped_ids']]
        group_map[group['group_id']] = dict(original_ids=group['ground_truth_chunk_ids'],
            mapped_ids=list(dict.fromkeys(cid for old in group['ground_truth_chunk_ids'] for cid in mappings[old]['mapped_ids'])),
            unresolved_ids=unresolved, complete=not unresolved)
    result = dict(protocol='Source-annotation span transfer across chunk-boundary changes; whole old span need not fit inside one new window.',
        identity_rule='Same file/page, exact NFC-decomposed letter/digit sequence after removal of exact leading printed-page artifact; protect decimal/percentage signature, require unique occurrence and complete source-character coverage.',
        relevance_rule='New chunk IDs whose source windows intersect an original gold source extent. This preserves the old annotated extent, not newly claim-specific expert labels. Tiny boundary overlaps can broaden relevance; disclose this transfer limitation.',
        unresolved_policy='Keep every query; Hit/MRR null for incomplete group mappings, never a miss or partial-gold score. Generation and reference-based RAGAS still run on all eligible records.',
        known_limits='Not new expert annotation; nine or other unresolved spans remain missing rather than inferred from question/reference/returned results.',
        mappings=mappings, groups=group_map,
        inputs={str(benchmark): sha(benchmark), str(legacy_path): sha(legacy_path), str(base / 'source_pages.json'): sha(base / 'source_pages.json'), str(base / 'corpus.json'): sha(base / 'corpus.json')},
        implementation_sha256=sha(Path(__file__)), benchmark_changed=False, retrieval_or_model_settings_changed=False)
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    (OUT / 'source_span_crosswalk.seal.json').write_text(json.dumps(dict(sha256=sha(target)), indent=2), encoding='utf-8')
    print(json.dumps(dict(mapped_legacy_spans=sum(bool(m['mapped_ids']) for m in mappings.values()), total_legacy_spans=len(mappings),
        complete_groups=sum(m['complete'] for m in group_map.values()), total_groups=70, unresolved_ids=[cid for cid,m in mappings.items() if not m['mapped_ids']])))


if __name__ == '__main__':
    main()
