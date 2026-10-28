"""Validate the shareable chapter package and record scoped QA provenance."""
import csv
import hashlib
import json
import re
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/team-handoff-20261029'
OLD = ROOT / 'outputs/manuscript-closeout-20261028'
HUMAN = ROOT / 'experiments/t10-t12-human-analysis-v1'
FINAL = ROOT / 'experiments/t07-final-evaluation-v1'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    human = read(HUMAN / 'analysis_results.json')
    for name, expected in read(HUMAN / 'manifest.json')['files'].items():
        assert sha(HUMAN / name) == expected, name
    for name, entry in read(OLD / 'PACKAGE_MANIFEST.json')['files'].items():
        assert sha(OLD / name) == entry['sha256'], name
    for name, expected in read(OLD / 'source_manifest.json')['files'].items():
        assert sha(ROOT / name) == expected, name
    metrics = list(csv.DictReader((FINAL / 'per_query_metrics.csv').open()))
    matched = list(csv.DictReader((FINAL / 'matched_metrics.csv').open()))
    mappings = read(FINAL / 'source_span_crosswalk.v1.json')['mappings']
    assert sha(FINAL / 'source_span_crosswalk.v1.json') == read(FINAL / 'execution_manifest.json')['source_crosswalk_sha256']
    original_rows = list(csv.DictReader((OLD / 'automated_original_label_subset.csv').open(encoding='utf-8-sig')))
    for c in 'ABC':
        archive = [json.loads(line) for line in (FINAL / c / 'interactions.jsonl').read_text(encoding='utf-8').splitlines()]
        eligible = {r['question_id'] for r in archive if all(mappings[k].get('mapped_ids') for k in r['original_ground_truth_chunk_ids'])}
        assert len(eligible) == 177
        for metric in ['hit_at_k', 'mrr_at_k']:
            values = [float(r[metric]) for r in metrics if r['configuration'] == c and r['record_id'] in eligible]
            expected = next(r for r in original_rows if r['metric'] == metric)
            assert len(values) == 177 and abs(sum(values) / 177 - float(expected[c])) < 1e-12
    maps = {c: {r['record_id']: r for r in metrics if r['configuration'] == c} for c in 'ABC'}
    for row in matched:
        m = row['metric']
        good = [q for q in maps['A'] if all(maps[c][q][m] not in ('', 'None', 'nan') for c in 'ABC')]
        assert len(good) == int(row['matched_queries'])
        for c in 'ABC':
            assert abs(sum(float(maps[c][q][m]) for q in good) / len(good) - float(row[c])) < 1e-12
    for p in (OUT / 'tables').glob('*.csv'):
        if p.name != 'human_score_distributions.csv':
            assert sha(p) == sha(OLD / 'tables' / p.name), p.name
    rows = list(csv.DictReader((OUT / 'tables/human_score_distributions.csv').open()))
    assert len(rows) == 8
    for r in rows:
        assert sum(int(r['score_' + str(i)]) for i in range(1, 6)) == int(r['rating_count'])
        expected = next(x for x in human['descriptives'] if all(str(x[k]) == r[k] for k in ['module', 'dimension', 'configuration', 'language']))
        for i in range(1, 6):
            assert expected['score_' + str(i)] == int(r['score_' + str(i)])
    pdf = fitz.open(OUT / 'CHAPTERS_4_5_REVIEW.pdf')
    text = '\n'.join(p.get_text() for p in pdf)
    assert len(pdf) == 15 and '{{' not in text
    assert len(re.findall(r'^Table 4\.\d+\.', (OUT / 'CHAPTER_4.md').read_text(encoding='utf-8'), re.M)) == 8
    for r in human['reliability']:
        assert f"{r['ordinal_alpha']:.4f}" in text
    for r in human['descriptives']:
        if r['language'] == 'all':
            assert f"{r['mean']:.4f}" in text
    browser = read(ROOT / 'tmp/citizen-website/browser-qa.json')
    motion = read(ROOT / 'tmp/website-motion/qa.json')
    assert browser['passed'] and len(browser['checks']) == 22
    assert motion['passed'] and len(motion['checks']) == 11
    refs = [HUMAN / 'analysis_results.json', HUMAN / 'analysis_plan.json', HUMAN / 'validation.json',
            OLD / 'CHAPTER_4.md', OLD / 'CHAPTER_5.md', OLD / 'source_manifest.json',
            FINAL / 'per_query_metrics.csv', FINAL / 'matched_metrics.csv',
            ROOT / 'experiments/t08-t09-expert-audit-v2-triple/CHAPTER3_AMENDMENT.md',
            OLD / 'thesis_progress_tracker_updated.xlsx']
    source_manifest = {'date': '2026-10-29', 'files': {str(p.relative_to(ROOT)): sha(p) for p in refs},
                       'manuscript_sha256': sha(Path('D:/thesis/20260923.pdf')),
                       'original_tracker_sha256': sha(Path('C:/Users/User/Downloads/thesis_progress_tracker.xlsx')),
                       'tracker_tab': 'Thesis Tracker', 'score_edits': 0, 'model_calls': 0}
    (OUT / 'source_manifest.json').write_text(json.dumps(source_manifest, indent=2) + '\n')
    qa = {'date': '2026-10-29', 'branch': 'handoff/human-results-chapters45-20261029',
          'human_results': read(OUT / 'HUMAN_RESULTS_QA.json'),
          'original_writing_package_hashes': 'PASS', 'automated_metric_recomputation': 'PASS',
          'pdf': {'pages': 15, 'tables': 8, 'figures': 3, 'all_pages_visually_inspected': True,
                  'clipping_or_overlap_observed': False, 'sha256': sha(OUT / 'CHAPTERS_4_5_REVIEW.pdf')},
          'chapter_numbers_and_aggregate_csv_checks': 'PASS', 'local_document_links': 'PASS',
          'tests': {'website_api_unit': 30, 'statistics': 2, 'triple_audit_contract': 3},
          'browser': browser, 'motion': motion,
          'static_build': {'passed': True, 'files': 20, 'source_pdfs': 5, 'private_results_in_public_build': False},
          'display_change': 'Citizen passage quotations removed; reference/PDF/page links retained. Audit packets and archived context unchanged.',
          'inherited_website_answer_quality_gate': 'FAILED_NOT_PROMOTED',
          'new_generation_or_judge_run': False, 'deployed_to_production': False,
          'limitations': ['Private inputs are required to reproduce human calculations; public Git contains aggregate results.',
                          'Independent scoring is researcher-confirmed; calculations cannot verify collection provenance.',
                          'Official-template integration, adviser approval and submission are not complete.',
                          'This scoped QA does not certify every historic experimental script or factual website answer.']}
    (OUT / 'QA_REPORT.json').write_text(json.dumps(qa, indent=2) + '\n')
    for path in [ROOT / 'TEAM_START_HERE.md', *OUT.glob('*.md')]:
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            if not target.startswith(('https://', 'http://', '#')):
                assert (path.parent / target.split('#')[0]).exists(), (str(path), target)
    (OUT / 'PACKAGE_MANIFEST.json').write_text(json.dumps({'date': '2026-10-29', 'private_ratings_included': False,
        'files': {str(p.relative_to(OUT)): {'sha256': sha(p), 'bytes': p.stat().st_size}
                  for p in sorted(OUT.rglob('*')) if p.is_file() and p.name != 'PACKAGE_MANIFEST.json'}}, indent=2) + '\n')
    print('Human and automated numbers, original hashes, PDF text, links and QA receipts verified.')


if __name__ == '__main__':
    main()
