"""Calibrate then stress-test exact source selection. Never starts a full grid."""
import collections
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.source_span_judge import VERSION, build_request, parse_selection
from scripts.calibrate_t07_structured_judge import read, sha, write, stats

OUT = ROOT / 'experiments/context-precision-source-span-validation-v4'


def prepare():
    reference = ROOT / 'experiments/t06-formal-development-validation-v4/methodology_and_tracker.json'
    refs = read(reference)
    assert sha(Path(refs['manuscript_path'])) == refs['manuscript_sha256']
    assert refs['authoritative_tab'] == 'Thesis Tracker'
    old = ROOT / 'experiments/context-precision-calibration-v2'
    controls = read(old / 'controls.snapshot.json')
    prior = read(old / 'protocol.json')
    assert len(controls) == 60 and sha(old / 'controls.snapshot.json') == prior['controls_sha256']
    grid = ROOT / 'experiments/t07-paired-grid-evaluator-v2'
    results = [json.loads(x) for x in (grid / 'judge_verdicts.jsonl').read_text(encoding='utf-8').splitlines()]
    records = {r['record_id']: r for r in [json.loads(x) for x in (grid / 'records.snapshot.jsonl').read_text(encoding='utf-8').splitlines()]}
    corpus = ROOT / 'experiments/chapter3-table-repaired-development-v1/corpus.json'
    chunks = {c['chunk_id']: c['text_content'] for c in read(corpus)}
    failures = [r for r in results if r['parsed'] is None]
    valid_cells = collections.defaultdict(list)
    for r in results:
        if r['parsed'] is not None:
            record = records[r['record_id']]
            valid_cells[(record['pillar'], record['language'])].append(r)
    assert len(valid_cells) == 15 and len(failures) == 110
    selected_valid = []
    for cell in sorted(valid_cells):
        selected_valid.extend(sorted(valid_cells[cell], key=lambda r: hashlib.sha256(
            ('source-span-stress-v4|' + r['record_id'] + '|' + r['chunk_id']).encode()).hexdigest())[:2])
    stress = []
    for r in failures + selected_valid:
        record = records[r['record_id']]
        stress.append(dict(case_id=r['record_id'] + '|' + r['chunk_id'], record_id=r['record_id'], chunk_id=r['chunk_id'],
            pillar=record['pillar'], language=record['language'], question=record['question'],
            reference_answer=record['reference_answer'], context=chunks[r['chunk_id']],
            old_status=r['status'], old_valid_verdict=r['parsed']['verdict'] if r['parsed'] else None))
    assert len(stress) == len({r['case_id'] for r in stress}) == 140
    protocol = dict(version=VERSION, settings=prior['settings'], model_digest=prior['model_digest'],
        input_hashes={str(p.relative_to(ROOT)): sha(p) for p in [reference, old / 'controls.snapshot.json', grid / 'judge_verdicts.jsonl', grid / 'records.snapshot.jsonl', corpus]},
        implementation_hashes={name: sha(ROOT / name) for name in ['src/source_span_judge.py', 'scripts/validate_source_span_judge.py']},
        selection_format='NONE means verdict 0; a source ID means verdict 1. Text recovered only by exact character pointers into the existing actual context.',
        source_spans='Deterministic adjacent groups of 32 whitespace words, preserving original character substrings. These are evaluator evidence pointers, NOT retrieval chunks. Corpus stays 120 tokenizer tokens /20 overlap.',
        criterion='Same v2 partial requested fact usefulness criterion; examples changed only for ID output representation.',
        calibration_gate='60 valid, >=55 correct, FP<=4, FN=0 after at most one format retry. These are necessary diagnostic criteria, not expert certification.',
        stress_policy='Only after calibration gate passes: all 110 formerly invalid pairs plus 30 old valid pairs, two per office/language chosen by fixed SHA256 order. Register before any call.',
        stress_gate='140 valid outputs; semantic disagreements with old valid judgments flagged, never treated as established errors or silently patched.',
        retry_policy='One format-only retry per invalid output; no retry for valid wrong judgments or network errors.',
        metric='RAGAS ranked average precision and manuscript 15-cell macro objective are unchanged; this experiment produces no grid objective.',
        limitations='Adaptive assistant-labeled controls from five groups; old valid judgments are not gold; exact evidence selection cannot guarantee semantic correctness.',
        methodology='20260923.pdf PDF33-34, development-only tuning and freeze before held-out. Main Thesis Tracker T06 is implementation; T07 is frozen A/B/C CSV comparison.',
        held_out_accessed=False, freeze=False, app_defaults_changed=False, automatic_full_grid=False)
    OUT.mkdir(exist_ok=True)
    if (OUT / 'protocol.json').exists():
        assert read(OUT / 'protocol.json') == protocol
        assert read(OUT / 'stress.snapshot.json') == stress
    else:
        write(OUT / 'protocol.json', protocol)
        write(OUT / 'controls.snapshot.json', controls)
        write(OUT / 'stress.snapshot.json', stress)
    return controls, stress, protocol


def main():
    import requests
    controls, stress, protocol = prepare()
    models = requests.get('http://localhost:11434/api/tags', timeout=10).json()['models']
    assert next(m for m in models if m['name'] == 'eboss-mistral:latest')['digest'] == protocol['model_digest']
    fd = os.open(OUT / 'judge.lock', os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    def log(message):
        print(message, flush=True)
        with (OUT / 'console.log').open('a', encoding='utf-8') as f:
            f.write(message + '\n')
    def run_stage(name, cases):
        target = OUT / (name + '.jsonl')
        results = [json.loads(x) for x in target.read_text(encoding='utf-8').splitlines()] if target.exists() else []
        assert len(results) == len({r['case_id'] for r in results})
        done = {r['case_id'] for r in results}
        for case in cases:
            if case['case_id'] in done:
                continue
            payload, spans = build_request(case['question'], case['reference_answer'], case['context'], protocol['settings'])
            result = {key: case[key] for key in ('case_id', 'pillar', 'language')}
            if name == 'calibration':
                result['expected_verdict'] = case['expected_verdict']
            else:
                result['old_valid_verdict'] = case['old_valid_verdict']
                result['old_status'] = case['old_status']
            result.update(parsed=None, attempts=[], source_spans=spans)
            for attempt in range(2):
                request = dict(payload)
                if attempt:
                    request['prompt'] += '\nFormat-only retry: return exactly reason and one legal evidence_span_id. Use NONE for no useful evidence. Apply the same criterion; do not change the task.'
                trace = dict(request=request, parsed=None)
                try:
                    response = requests.post('http://localhost:11434/api/generate', json=request, timeout=120)
                    response.raise_for_status()
                    data = response.json()
                    trace['response'] = {k: v for k, v in data.items() if k != 'context'}
                    parsed, error = parse_selection(data['response'], case['context'], spans)
                    if data.get('done_reason') == 'length':
                        parsed, error = None, 'TRUNCATED'
                    trace.update(parsed=parsed, error=error)
                except Exception as exc:
                    trace['error'] = str(exc)
                    result['attempts'].append(trace)
                    break
                result['attempts'].append(trace)
                if parsed is not None:
                    result['parsed'] = parsed
                    break
            with target.open('a', encoding='utf-8') as f:
                f.write(json.dumps(result, ensure_ascii=False, allow_nan=False) + '\n')
            results.append(result)
            write(OUT / 'progress.json', dict(stage=name, completed=len(results), total=len(cases), latest=case['case_id']))
            log(f'{name} {len(results)}/{len(cases)} {case["case_id"]} ' + ('VALID' if result['parsed'] else 'INVALID'))
        return results
    try:
        results = run_stage('calibration', controls)
        overall = stats(results)
        passed = overall['valid'] == 60 and overall['correct'] >= 55 and overall['FP'] <= 4 and overall['FN'] == 0
        write(OUT / 'calibration_summary.json', dict(overall=overall, screening_gate_passed=passed,
              disagreements=[r['case_id'] for r in results if r['parsed'] and r['parsed']['verdict'] != r['expected_verdict']],
              held_out_accessed=False, independent_validation=False))
        if not passed:
            write(OUT / 'decision.json', dict(status='CALIBRATION_FAILED_NO_STRESS_OR_GRID', t06='IMPLEMENTATION_COMPLETE', t07='PENDING'))
            log('Calibration screening failed. Stop; no stress test or full grid.')
            return
        log('Calibration screening passed. Continue only the preregistered 140-pair stress test.')
        results = run_stage('stress', stress)
        valid = [r for r in results if r['parsed'] is not None]
        differences = [r['case_id'] for r in valid if r['old_valid_verdict'] is not None and r['old_valid_verdict'] != r['parsed']['verdict']]
        write(OUT / 'stress_summary.json', dict(total=140, valid=len(valid), invalid=140 - len(valid),
              differences_from_old_valid_judgments=differences, old_judgments_are_not_gold=True,
              held_out_accessed=False, selection_allowed=False))
        write(OUT / 'decision.json', dict(status='STRESS_FINISHED_REVIEW_REQUIRED' if len(valid) == 140 else 'STRESS_INVALIDS_NO_PROMOTION',
              t06='IMPLEMENTATION_COMPLETE', t07='PENDING', full_grid_started=False, held_out_accessed=False))
        assert all(sha(ROOT / name) == value for name, value in protocol['input_hashes'].items())
        log('Calibration and stress test finished. Review semantic differences; no full grid or freeze started.')
    finally:
        (OUT / 'judge.lock').unlink()


if __name__ == '__main__':
    main()
