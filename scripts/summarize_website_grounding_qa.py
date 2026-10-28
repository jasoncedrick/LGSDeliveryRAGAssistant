"""Summarize the exploratory website run without assigning factual accuracy."""
import argparse
import collections
import csv
import hashlib
import json
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default='tmp/grounding-v4-full')
    parser.add_argument('--output', default='outputs/website-grounding-qa-20261028')
    args = parser.parse_args()
    source, output = ROOT / args.input, ROOT / args.output
    manifest = json.loads((source / 'manifest.json').read_text())
    rows = [json.loads(line) for line in (source / 'results.jsonl').read_text().splitlines()]
    ids = [r['id'] for r in rows]
    if len(ids) != len(set(ids)) or set(ids) != set(manifest['case_ids']) or len(ids) != 200:
        raise ValueError('Expected exactly the 200 registered unique cases; run incomplete or inconsistent')
    for name, expected in manifest['runtime_hashes'].items():
        if sha(ROOT / name) != expected:
            raise ValueError('Runtime differs from tested candidate: ' + name)
    if sha(ROOT / 'config/website_response_language_v4.json') != manifest['prompt_sha256']:
        raise ValueError('Tested prompt differs from current candidate')
    rows.sort(key=lambda r: r['id'])
    records = []
    for row in rows:
        candidate, baseline = row['candidate'], row['baseline']
        diag = candidate.get('diagnostics', {})
        answer = candidate.get('answer', '') or ''
        allowed = {c['citation'] for c in candidate.get('citations', [])}
        mentioned = set(re.findall(r'\bS\d+\b', answer))
        records.append({
            'id': row['id'], 'category': row['category'],
            'baseline_status': baseline['status'], 'candidate_status': candidate['status'],
            'retrieval_started': candidate.get('retrieval_started', False),
            'generation_started': candidate.get('generation_started', False),
            'coverage_issue': diag.get('coverage_issue', ''),
            'response_language_selection': diag.get('response_language', ''),
            'citation_validator_flag': diag.get('citation_labels_valid', ''),
            'unknown_source_labels': '|'.join(sorted(mentioned - allowed)),
            'internal_id_in_answer': bool(re.search(r'\b(?:DEV120|CHUNK)-[A-Z]', answer)),
            'candidate_words': len(answer.split()),
            'candidate_elapsed_seconds': row['elapsed_seconds'],
        })
    generated = [r for r in records if r['generation_started']]
    summary = {
        'scope': 'Exploratory post-study website regression, not a held-out result or accuracy estimate',
        'execution': 'COMPLETE', 'unique_queries': len(rows),
        'quality_gate': 'FAILED_NOT_PROMOTED',
        'reason': 'Observed unsupported claims and response-language failures remain. Passing software checks does not certify factual correctness.',
        'input_and_runtime_manifest': manifest,
        'results_sha256': sha(source / 'results.jsonl'),
        'progress_sha256': sha(source / 'progress.log'),
        'baseline_status_counts': dict(collections.Counter(r['baseline_status'] for r in records)),
        'candidate_status_counts': dict(collections.Counter(r['candidate_status'] for r in records)),
        'candidate_generated_count': len(generated),
        'candidate_retrieved_count': sum(bool(r['retrieval_started']) for r in records),
        'baseline_citation_validator_false_ids': [r['id'] for r in rows if r['baseline'].get('citation_labels_valid') is False],
        'baseline_internal_id_leak_ids': [r['id'] for r in rows if re.search(r'\b(?:DEV120|CHUNK)-[A-Z]', r['baseline'].get('answer', '') or '')],
        'coverage_issue_counts': dict(collections.Counter(r['coverage_issue'] for r in records if r['coverage_issue'])),
        'citation_validator_false_ids': [r['id'] for r in records if r['citation_validator_flag'] is False],
        'unknown_source_label_ids': [r['id'] for r in records if r['unknown_source_labels']],
        'internal_id_leak_ids': [r['id'] for r in records if r['internal_id_in_answer']],
        'elapsed_seconds_mean': round(statistics.mean(r['elapsed_seconds'] for r in rows), 3),
        'elapsed_seconds_median': round(statistics.median(r['elapsed_seconds'] for r in rows), 3),
        'software_checks': {'api_unit_tests_passed': 30, 'browser_checks_passed': 21,
                            'motion_checks_passed': 11, 'static_build': 'PASS'},
        'limitations': [
            'Status ANSWERED and valid source labels are not factual-quality judgments.',
            'Selected failures were inspected; no complete manual correctness labeling of all 200 answers.',
            'The candidate is evaluated directly through the pipeline, not 200 new production HTTP requests.',
            'Run is sequential, not a concurrent load test.',
            'Thirteen matching-hash focused cases are reused, not regenerated.',
            'Language selection metadata does not establish actual output-language fidelity.',
            'More abstentions can conceal retrieval failures and reduce useful coverage.',
            'Baseline archive lacks a pinned backend configuration; timing is descriptive, not a controlled speed comparison.',
            'No RAGAS judge, frozen experiment change, or production promotion occurred.',
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    with (output / 'case_statuses.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    print(json.dumps({k: v for k, v in summary.items() if k not in ['input_and_runtime_manifest', 'limitations']}, indent=2))


if __name__ == '__main__':
    main()
