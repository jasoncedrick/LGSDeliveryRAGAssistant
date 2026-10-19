"""Exact source-identity audit only; never writes replacement benchmark labels."""
import collections
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


def canonical(text):
    # Identity normalization only; preserve punctuation, numbers and word content.
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', text)).strip().casefold()


def main():
    registration = read(OUT / 'candidate_registration.json')
    assert sha(OUT / 'candidate_registration.json') == read(OUT / 'registration_seal.json')['candidate_registration_sha256']
    assert all(sha(ROOT / path) == value for path, value in registration['file_hashes'].items())
    test_path = Path(registration['held_out_path'])
    test_hash = sha(test_path)
    groups = read(test_path)
    old_path = Path('D:/thesis/LGSDeliveryRAGAssistant-main/data/eboss_corpus_chunks_v1.json')
    old = {c['chunk_id']: c for c in read(old_path)}
    corpus_path = ROOT / 'experiments/chapter3-table-repaired-development-v1/corpus.json'
    current = read(corpus_path)
    expected_ids = sorted({cid for g in groups for cid in g['ground_truth_chunk_ids']})
    findings = []
    for cid in expected_ids:
        original = old.get(cid)
        if original is None:
            findings.append(dict(legacy_id=cid, status='NOT_IN_LEGACY_SOURCE_CORPUS', exact_candidates=[]))
            continue
        candidates = [c for c in current if c['file_source'] == original['file_source'] and c.get('pdf_relative_page') == original.get('pdf_relative_page')]
        text = canonical(original['text_content'])
        # Entire legacy span must actually occur within a candidate passage.
        exact = [c['chunk_id'] for c in candidates if text and text in canonical(c['text_content'])]
        findings.append(dict(legacy_id=cid, file_source=original['file_source'], pdf_relative_page=original.get('pdf_relative_page'),
            legacy_text_sha256=hashlib.sha256(original['text_content'].encode()).hexdigest(),
            status='EXACT_FULL_SPAN_FOUND' if exact else 'NO_EXACT_FULL_SPAN_IN_CURRENT_CHUNK',
            exact_candidates=exact, same_page_candidate_count=len(candidates)))
    missing = {r['legacy_id'] for r in findings if not r['exact_candidates']}
    summary = dict(legacy_gold_ids=len(expected_ids), findings_by_status=dict(collections.Counter(r['status'] for r in findings)),
        groups_with_all_spans_exactly_resolvable=sum(not (set(g['ground_truth_chunk_ids']) & missing) for g in groups),
        split_tag_values=dict(collections.Counter(g.get('split') for g in groups)),
        split_tag_interpretation='held_out_test is the existing descriptive held-out tag, not evidence of group leakage. The initial parser did not recognize this spelling. The substantive unresolved issue is gold/source identity.',
        findings=findings, benchmark_sha256=test_hash, legacy_corpus_sha256=sha(old_path), current_corpus_sha256=sha(corpus_path),
        labels_changed=False, mapping_applied=False, final_inference_started=False,
        rule='NFC + whitespace + case identity comparison; punctuation, numbers and wording preserved. No fuzzy matching, page-wide relabeling or question/answer-based selection.',
        interpretation='An ID rename alone cannot repair incompatible source spans. Exact matches are candidates only, not an applied or manually certified replacement benchmark.')
    assert not (OUT / 'legacy_gold_identity_audit.json').exists()
    (OUT / 'legacy_gold_identity_audit.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    assert sha(test_path) == test_hash
    print(json.dumps({k: v for k, v in summary.items() if k != 'findings'}, indent=2))


if __name__ == '__main__':
    main()
