"""Small, versioned output-format experiment; never promotes a T07 configuration."""
import collections
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.context_precision_judge_v2 import build_prompt, FORMAT_RETRY_SUFFIX, PROMPT_TEMPLATE
from src.offline_judge_grounding import parse_grounded_verdict

SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'properties': {'reason': {'type': 'string'}, 'verdict': {'type': 'string', 'enum': ['0', '1']},
                   'evidence_quotes': {'type': 'array', 'items': {'type': 'string'}}},
    'required': ['reason', 'verdict', 'evidence_quotes'],
}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    tmp.replace(path)


def stats(results):
    valid = [r for r in results if r['parsed'] is not None]
    return dict(total=len(results), valid=len(valid), invalid=len(results) - len(valid),
        correct=sum(r['parsed']['verdict'] == r['expected_verdict'] for r in valid),
        FP=sum(r['parsed']['verdict'] == '1' and r['expected_verdict'] == '0' for r in valid),
        FN=sum(r['parsed']['verdict'] == '0' and r['expected_verdict'] == '1' for r in valid),
        failure_types=dict(collections.Counter(r['attempts'][-1].get('error') for r in results if r['parsed'] is None)))


def main():
    import requests
    old = ROOT / 'experiments/context-precision-calibration-v2'
    out = ROOT / 'experiments/context-precision-calibration-v3-structured'
    refs = ROOT / 'experiments/t06-formal-development-validation-v4/methodology_and_tracker.json'
    grounding = read(refs)
    assert sha(Path(grounding['manuscript_path'])) == grounding['manuscript_sha256']
    assert grounding['authoritative_tab'] == 'Thesis Tracker'
    old_protocol = read(old / 'protocol.json')
    cases = read(old / 'controls.snapshot.json')
    assert len(cases) == 60 and len({c['case_id'] for c in cases}) == 60
    assert sha(old / 'controls.snapshot.json') == old_protocol['controls_sha256']
    tags = requests.get('http://localhost:11434/api/tags', timeout=10).json()['models']
    model = next(m for m in tags if m['name'] == 'eboss-mistral:latest')
    assert model['digest'] == old_protocol['model_digest']
    protocol = dict(version='context-precision-v2-prompt-with-structured-format-v3',
        sole_intervention='Ollama format JSON schema; same v2 usefulness prompt, model, options, controls, quote validator and single format retry.',
        schema=SCHEMA, model_digest=model['digest'], settings=old_protocol['settings'],
        template_sha256=hashlib.sha256(PROMPT_TEMPLATE.encode()).hexdigest(),
        controls_sha256=sha(old / 'controls.snapshot.json'), reference_evidence_sha256=sha(refs),
        implementation_sha256=sha(Path(__file__)),
        docs='https://docs.ollama.com/capabilities/structured-outputs',
        calibration_gate='All 60 valid after at most one format retry; at least 55 correct; FP <=4, FN=0. Necessary screening only; not automatic acceptance.',
        next_gate='If screening passes, predeclare a stress test covering previous invalid and valid grid outputs before any full rescore. Review semantic errors independently of JSON validity.',
        retry_policy='One format-only retry only after invalid output; no retry of valid disagreements or network errors.',
        limitations='Same assistant-labeled controls reused adaptively; five groups, not 60 independent groups. Not independent expert validation.',
        methodology='20260923.pdf PDF33-34: development-only evaluator work, select using Context Precision, freeze before held-out. Main Thesis Tracker T07 archived in references.',
        held_out_accessed=False, app_defaults_changed=False, full_grid_started=False)
    out.mkdir(exist_ok=True)
    if (out / 'protocol.json').exists():
        assert read(out / 'protocol.json') == protocol
    else:
        write(out / 'protocol.json', protocol)
        (out / 'controls.snapshot.json').write_bytes((old / 'controls.snapshot.json').read_bytes())
        (out / 'prompt_template.txt').write_text(PROMPT_TEMPLATE, encoding='utf-8')
    lock = out / 'judge.lock'
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    def log(text):
        print(text, flush=True)
        with (out / 'console.log').open('a', encoding='utf-8') as handle:
            handle.write(text + '\n')
    try:
        file = out / 'results.jsonl'
        results = [json.loads(x) for x in file.read_text(encoding='utf-8').splitlines()] if file.exists() else []
        assert len(results) == len({r['case_id'] for r in results})
        done = {r['case_id'] for r in results}
        started = time.monotonic()
        for case in cases:
            if case['case_id'] in done:
                continue
            result = dict(case_id=case['case_id'], pillar=case['pillar'], language=case['language'],
                          expected_verdict=case['expected_verdict'], parsed=None, attempts=[])
            prompt = build_prompt(case['question'], case['reference_answer'], case['context'])
            for attempt in range(2):
                payload = dict(model='eboss-mistral', prompt=prompt + (FORMAT_RETRY_SUFFIX if attempt else ''),
                               stream=False, options=protocol['settings'], format=SCHEMA)
                trace = dict(request=payload, parsed=None)
                try:
                    response = requests.post('http://localhost:11434/api/generate', json=payload, timeout=120)
                    response.raise_for_status()
                    data = response.json()
                    trace['response'] = {k: v for k, v in data.items() if k != 'context'}
                    parsed, error = parse_grounded_verdict(data['response'], case['context'])
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
            with file.open('a', encoding='utf-8') as handle:
                handle.write(json.dumps(result, ensure_ascii=False, allow_nan=False) + '\n')
            results.append(result)
            write(out / 'progress.json', dict(completed=len(results), total=60,
                  elapsed_seconds=round(time.monotonic() - started, 1), latest=case['case_id']))
            log(f'{len(results)}/60 {case["case_id"]} ' + ('VALID' if result['parsed'] else 'INVALID'))
        overall = stats(results)
        gate = overall['valid'] == 60 and overall['correct'] >= 55 and overall['FP'] <= 4 and overall['FN'] == 0
        write(out / 'summary.json', dict(overall=overall, screening_gate_passed=gate,
            by_office_language={office + '|' + language: stats([r for r in results if r['pillar'] == office and r['language'] == language])
                for office in sorted({r['pillar'] for r in results}) for language in ('english', 'taglish', 'bislish')},
            old_v2_baseline=read(ROOT / 'experiments/context-precision-calibration-v2-format-retry/summary.json'),
            selection_allowed=False, held_out_accessed=False, freeze=False,
            decision='READY_FOR_STRESS_TEST_REVIEW_ONLY' if gate else 'NOT_READY_FOR_FULL_GRID'))
        assert sha(old / 'controls.snapshot.json') == protocol['controls_sha256']
        log('Calibration finished. ' + ('Screening passed; stress-test review next.' if gate else 'Screening failed; no full grid started.'))
    finally:
        lock.unlink()


if __name__ == '__main__':
    main()
