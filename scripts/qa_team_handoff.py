"""Replay preserved human statistics locally without changing source ratings.

Requires the private input snapshot and issued packet key; neither is published.
No model calls. Use a new ignored output directory for every verification.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import analyze_human_audit as analysis

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='tmp/team-handoff-20261029/human-replay')
    args = parser.parse_args()
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to((ROOT / 'tmp').resolve()) or output.exists():
        raise ValueError('Use a new directory under ignored tmp/')
    original = ROOT / 'experiments/t10-t12-human-analysis-v1'
    manifest = json.loads((original / 'manifest.json').read_text())
    for relative, expected in manifest['files'].items():
        path = original / relative
        if not path.exists():
            raise FileNotFoundError('Private archive needed for replay: ' + str(path))
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, relative
    analysis.SOURCE = original / 'private/input_snapshot'
    analysis.OUT = output
    analysis.run()
    expected = json.loads((original / 'analysis_results.json').read_text())
    actual = json.loads((output / 'analysis_results.json').read_text())
    for section in ['descriptives', 'reliability', 'comparisons', 'no_claim_sensitivity', 'seed']:
        assert actual[section] == expected[section], section
    for name in ['descriptive_scores.csv', 'reliability.csv', 'paired_comparisons.csv', 'no_claim_sensitivity.csv']:
        assert (original / name).read_bytes() == (output / name).read_bytes(), name
    rows = list(csv.DictReader((original / 'private/ratings_long.csv').open(encoding='utf-8-sig')))
    assert len(rows) == 1320
    assert len({(r['module'], r['answer_id'], r['rater']) for r in rows}) == 780
    assert len({r['group_id'] for r in rows}) == 20
    for relative, expected_hash in manifest['files'].items():
        assert hashlib.sha256((original / relative).read_bytes()).hexdigest() == expected_hash
    report = {
        'date': '2026-10-29', 'passed': True, 'verified_original_manifest_files': len(manifest['files']),
        'records': 780, 'dimension_scores': 1320, 'scenario_groups': 20,
        'recomputed_descriptives_reliability_comparisons_and_sensitivity': 'EXACT_MATCH',
        'aggregate_csv_files': 'BYTE_IDENTICAL', 'original_files_after_replay': 'UNCHANGED',
        'model_calls': 0, 'score_edits': 0, 'imputation': False,
        'provenance': 'Researcher-confirmed independent scoring; replay verifies data and calculations, not collection independence.',
        'runtime_versions': actual['versions'],
    }
    (output / 'REPLAY_QA.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
