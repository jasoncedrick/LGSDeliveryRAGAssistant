"""Prepare a label-hidden control packet and compare independently entered reviews.

No model calls, held-out access, replacement RAGAS scores or automatic selection.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / 'experiments/t07-independent-judge-review-v1'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def validate_review(review, snapshot):
    if review.get('independent_human_review_completed') is not True:
        raise ValueError('Human review is not marked complete. Do not auto-fill this attestation.')
    if not isinstance(review.get('review_basis'), str) or not review['review_basis'].strip():
        raise ValueError('Explain how the reviewer is independent of the automatic judgments; no name is needed.')
    rows = review.get('items', [])
    original = {r['audit_id']: r for r in snapshot['items']}
    if len(rows) != len(original) or {r['audit_id'] for r in rows} != set(original):
        raise ValueError('Missing, duplicate or unknown audit IDs.')
    result = {}
    for row in rows:
        frozen = original[row['audit_id']]
        for key, value in frozen.items():
            if key not in ('decision', 'notes') and row.get(key) != value:
                raise ValueError('Review source fields changed: ' + row['audit_id'] + '/' + key)
        if row.get('decision') not in ('useful', 'not_useful', 'uncertain'):
            raise ValueError('Pending/invalid decision: ' + row['audit_id'])
        if not isinstance(row.get('notes'), str) or not row['notes'].strip():
            raise ValueError('Add a brief context-based reason for ' + row['audit_id'])
        result[row['audit_id']] = row['decision']
    return result


def prepare():
    refs = ROOT / 'experiments/t06-formal-development-validation-v4/methodology_and_tracker.json'
    grounding = read(refs)
    assert sha(Path(grounding['manuscript_path'])) == grounding['manuscript_sha256']
    assert grounding['authoritative_tab'] == 'Thesis Tracker'
    controls_path = ROOT / 'experiments/context-precision-calibration-v2/controls.snapshot.json'
    controls = read(controls_path)
    assert len(controls) == len({c['case_id'] for c in controls}) == 60
    assert not PACKET.exists(), 'Preserve an existing packet and edits; use a new version.'
    controls.sort(key=lambda c: hashlib.sha256(('T07-control-review-v1|' + c['case_id']).encode()).hexdigest())
    items, key = [], []
    for number, control in enumerate(controls, 1):
        aid = f'AUDIT-{number:03d}'
        items.append(dict(audit_id=aid, office=control['pillar'], language=control['language'],
            question=control['question'], reference_answer=control['reference_answer'],
            actual_retrieved_context=control['context'], decision=None, notes=''))
        key.append(dict(audit_id=aid, original_case_id=control['case_id'],
            previous_assistant_label=control['expected_verdict'], chunk_id=control['chunk_id'],
            source_pdf=control['source_pdf'], pdf_relative_page=control['pdf_relative_page'],
            source_pdf_sha256=control['source_pdf_sha256']))
    packet = dict(independent_human_review_completed=False, review_basis='',
        instructions='Edit decision and notes only for each item; useful / not_useful / uncertain. Compare actual context against the requested fact. A reference is not evidence that the context contains it. Do not open the private key or old model judgments while reviewing. Complete the top-level attestation and review_basis only when genuinely reviewed. No reviewer name is required.',
        items=items)
    PACKET.mkdir()
    write(PACKET / 'human_review.json', packet)
    write(PACKET / 'packet.snapshot.json', packet)
    write(PACKET / 'PRIVATE_comparison_key.json', key)
    sources = {
        'v2_after_format_retry': ROOT / 'experiments/context-precision-calibration-v2-format-retry/results.with_retries.json',
        'v3_structured': ROOT / 'experiments/context-precision-calibration-v3-structured/results.jsonl',
        'v4_source_span': ROOT / 'experiments/context-precision-source-span-validation-v4/calibration.jsonl',
    }
    write(PACKET / 'protocol.json', dict(
        purpose='Independent usefulness review of existing adaptive development controls; not final employee ratings or held-out evaluation.',
        control_count=60, distinct_groups=5, blinding='Model outputs, previous labels and original case IDs are omitted from the review form. Separate key retained. Prior reports may be known, so do not claim formal double blinding.',
        sources={name: dict(path=str(path.relative_to(ROOT)), sha256=sha(path)) for name, path in sources.items()},
        source_controls_sha256=sha(controls_path), references_sha256=sha(refs),
        packet_snapshot_sha256=sha(PACKET / 'packet.snapshot.json'), private_key_sha256=sha(PACKET / 'PRIVATE_comparison_key.json'),
        rule='Partial evidence for a requested fact is useful; topic or service heading alone is not. Preserve source ambiguity and use uncertain where needed.',
        scoring='Report validity, disagreement and uncertainty separately. No automatic judge adoption, no replacement of missing grid scores, no selection or freeze.',
        methodology='20260923.pdf PDF33-34: development objective, leakage prevention and freeze before held-out; main Thesis Tracker T07.',
        provenance='This independent check is a recommended validation response to observed judge failures, not an additional literal manuscript requirement.',
        held_out_accessed=False, app_defaults_changed=False))
    print('Prepared 60-item review. Human input remains pending: ' + str(PACKET / 'human_review.json'))


def compare(output_name):
    if Path(output_name).name != output_name:
        raise ValueError('Use a fresh experiment folder name.')
    protocol = read(PACKET / 'protocol.json')
    assert sha(PACKET / 'packet.snapshot.json') == protocol['packet_snapshot_sha256']
    assert sha(PACKET / 'PRIVATE_comparison_key.json') == protocol['private_key_sha256']
    decisions = validate_review(read(PACKET / 'human_review.json'), read(PACKET / 'packet.snapshot.json'))
    mapping = read(PACKET / 'PRIVATE_comparison_key.json')
    out = ROOT / 'experiments' / output_name
    if out.exists():
        raise ValueError('Output exists; preserve it and choose a new name.')
    summaries = {}
    for version, source in protocol['sources'].items():
        path = ROOT / source['path']
        assert sha(path) == source['sha256']
        records = read(path) if path.suffix == '.json' else [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines()]
        records = {r['case_id']: r for r in records}
        rows = []
        for item in mapping:
            record = records[item['original_case_id']]
            independent = decisions[item['audit_id']]
            observed = record['parsed']['verdict'] if record['parsed'] else None
            expected = {'useful': '1', 'not_useful': '0', 'uncertain': None}[independent]
            rows.append(dict(audit_id=item['audit_id'], independent_decision=independent,
                old_assistant_label=item['previous_assistant_label'], judge_verdict=observed,
                agrees=observed == expected if observed is not None and expected is not None else None))
        evaluable = [r for r in rows if r['agrees'] is not None]
        summaries[version] = dict(total=60, valid=sum(r['judge_verdict'] is not None for r in rows),
            uncertain_human=sum(r['independent_decision'] == 'uncertain' for r in rows),
            evaluable=len(evaluable), agrees=sum(r['agrees'] for r in evaluable),
            rows=rows)
    out.mkdir()
    write(out / 'independent_review_comparison.json', dict(results=summaries,
        reviewed_packet_sha256=sha(PACKET / 'human_review.json'), selection_allowed=False,
        interpretation='Validation evidence only; old automatic labels are not human gold. Uncertain and invalid outcomes remain separate. Review all disagreements before any evaluator adoption.',
        held_out_accessed=False))
    print('Independent comparison saved without altering any archived score: ' + str(out))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--compare-output')
    args = parser.parse_args()
    if args.prepare == bool(args.compare_output):
        parser.error('Choose exactly one: --prepare or --compare-output NEW_FOLDER')
    if args.prepare:
        prepare()
    else:
        compare(args.compare_output)
