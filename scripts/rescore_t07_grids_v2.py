"""Paired development-grid rescore with one fixed, audited offline evaluator.

Preparation is read-only for inputs. Running is resumable only against identical
inputs, prompt and model settings. No retrieval, generation or held-out access.
"""
import argparse
import collections
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ['RAGAS_DO_NOT_TRACK'] = 'true'
from src.context_precision_judge_v2 import VERSION, PROMPT_TEMPLATE, FORMAT_RETRY_SUFFIX, build_prompt
from src.offline_judge_grounding import parse_grounded_verdict

OUT = ROOT / 'experiments/t07-paired-grid-evaluator-v2'
SETTINGS = dict(temperature=0, top_p=0, num_ctx=8192, num_predict=1024, num_thread=4)
MODEL_DIGEST = '39d9f435aeed825a340db73dfba9e7ce346664aa00727c9066bb1f0352406a6f'
INPUTS = {
    'original': ROOT / 'experiments/t07-development-grid-format-retry-v2/rankings.jsonl',
    'punctuation': ROOT / 'experiments/punctuation-context-precision-format-retry-v2/rankings.jsonl',
    'records': ROOT / 'experiments/t06-formal-development-validation-v4/interactions.corrected_references.jsonl',
    'corpus': ROOT / 'experiments/chapter3-table-repaired-development-v1/corpus.json',
    'grid_protocol': ROOT / 'experiments/t07-development-grid-format-retry-v2/protocol.json',
    'references': ROOT / 'experiments/t06-formal-development-validation-v4/methodology_and_tracker.json',
    'manuscript': Path('D:/thesis/20260923.pdf'),
}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def lines(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    temporary.replace(path)


def aggregate(rankings, records, verdicts, metric):
    results = []
    for grid in range(17):
        rows = [r for r in rankings if r['grid_id'] == grid]
        assert len(rows) == 90 and len({r['record_id'] for r in rows}) == 90
        for k in (3, 5):
            cells = collections.defaultdict(list)
            failures = []
            for row in rows:
                rid = row['record_id']
                record = records[rid]
                ids = row['rankings'][str(k)]
                values = [verdicts.get((rid, cid)) for cid in ids]
                score = 0.0 if not ids else (
                    float(metric._calculate_average_precision(values))
                    if all(v is not None for v in values) else None)
                if score is None:
                    failures.append(rid)
                cells[record['pillar'] + '|' + record['language']].append(score)
            assert len(cells) == 15 and all(len(v) == 6 for v in cells.values())
            means = {c: sum(v) / 6 if all(x is not None for x in v) else None for c, v in cells.items()}
            objective = sum(means.values()) / 15 if not failures else None
            results.append(dict(grid_id=grid, weights=rows[0]['weights'], k=k, J=objective,
                                cell_means=means, failed_record_ids=failures))
    return results


def prepare():
    references = read(INPUTS['references'])
    assert sha(INPUTS['manuscript']) == references['manuscript_sha256']
    assert references['authoritative_tab'] == 'Thesis Tracker'
    tracker = Path(references['tracker_path'])
    if tracker.exists():
        assert sha(tracker) == references['tracker_sha256']
    records_list = lines(INPUTS['records'])
    records = {r['record_id']: r for r in records_list}
    assert len(records) == len(records_list) == 90
    assert len({r['question_group_id'] for r in records_list}) == 30
    chunks = {c['chunk_id']: c['text_content'] for c in read(INPUTS['corpus'])}
    grids = {name: [r for r in lines(INPUTS[name]) if r['configuration'] == 'B']
             for name in ('original', 'punctuation')}
    grid_protocol = read(INPUTS['grid_protocol'])
    assert grid_protocol['k_values'] == [3, 5] and len(grid_protocol['weight_grid']) == 17
    for rows in grids.values():
        assert len(rows) == 90 * 17
        assert len({(r['grid_id'], r['record_id']) for r in rows}) == len(rows)
        for row in rows:
            assert row['weights'] == grid_protocol['weight_grid'][row['grid_id']]
            assert row['record_id'] in records
            assert row['rankings']['3'] == row['rankings']['5'][:3]
            assert len(row['rankings']['5']) in (0, 5)
            assert all(cid in chunks for cid in row['rankings']['5'])
    pairs = sorted({(r['record_id'], cid) for rows in grids.values()
                    for r in rows for cid in r['rankings']['5']})
    protocol = dict(
        evaluator=VERSION, model='eboss-mistral', model_digest=MODEL_DIGEST, settings=SETTINGS,
        prompt_sha256=hashlib.sha256(PROMPT_TEMPLATE.encode()).hexdigest(),
        format_retry_suffix_sha256=hashlib.sha256(FORMAT_RETRY_SUFFIX.encode()).hexdigest(),
        input_hashes={name: sha(path) for name, path in INPUTS.items()},
        implementation_hashes={name: sha(ROOT / name) for name in (
            'scripts/rescore_t07_grids_v2.py', 'src/context_precision_judge_v2.py',
            'src/offline_judge_grounding.py')},
        unique_query_context_pairs=len(pairs), development_queries=90, development_groups=30,
        conditions_per_grid=34, weight_grid=grid_protocol['weight_grid'], k_values=[3, 5],
        selection='RAGAS 0.1.5 ContextPrecision AP; macro mean of 15 cells of six queries each.',
        tie_break='Exact objective tie: original tokenizer, then declared grid order, then K=3.',
        error_policy='Stopped queries zero; judge errors null. No selection until all 68 conditions complete.',
        retry_policy='At most one format-only retry for an invalid response; never retry a valid disagreement.',
        cache_policy='Union of both grids: each identical query/context judged once. No old evaluator scores reused.',
        methodology='20260923.pdf PDF28,30,32-34; archived main Thesis Tracker T06/T07 rows.',
        calibration_limitations='Adaptive controls: 55/60 agreement, four false positives and one invalid; not expert certification.',
        held_out_accessed=False, freeze=False, app_defaults_changed=False,
        chunk_tokens=120, overlap_tokens=20, scoring_unit='chunk')
    OUT.mkdir(exist_ok=True)
    if (OUT / 'protocol.json').exists():
        assert read(OUT / 'protocol.json') == protocol, 'Inputs or implementation changed; create a new version.'
    else:
        write(OUT / 'protocol.json', protocol)
        (OUT / 'prompt_template.txt').write_text(PROMPT_TEMPLATE, encoding='utf-8')
        for name in ('original', 'punctuation', 'records', 'grid_protocol', 'references'):
            (OUT / (name + '.snapshot' + INPUTS[name].suffix)).write_bytes(INPUTS[name].read_bytes())
    return records, chunks, grids, pairs, protocol


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only', action='store_true')
    args = parser.parse_args()
    records, chunks, grids, pairs, protocol = prepare()
    if args.prepare_only:
        print(json.dumps(dict(output=str(OUT), pairs=len(pairs), conditions=68, held_out_accessed=False)), flush=True)
        return
    import requests
    from ragas.metrics import context_precision
    model = next(m for m in requests.get('http://localhost:11434/api/tags', timeout=10).json()['models']
                 if m['name'] == 'eboss-mistral:latest')
    assert model['digest'] == MODEL_DIGEST
    lock = OUT / 'judge.lock'
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    started = time.monotonic()
    def log(message):
        print(message, flush=True)
        with (OUT / 'console.log').open('a', encoding='utf-8') as handle:
            handle.write(message + '\n')
    try:
        result_file = OUT / 'judge_verdicts.jsonl'
        cached = {(r['record_id'], r['chunk_id']): r for r in lines(result_file)} if result_file.exists() else {}
        verdicts = {}
        log(f'Start/resume: {len(cached)} archived / {len(pairs)} unique pairs; 68 grid conditions; evaluator {VERSION}')
        for number, (rid, cid) in enumerate(pairs, 1):
            record, context = records[rid], chunks[cid]
            prompt = build_prompt(record['question'], record['reference_answer'], context)
            key = hashlib.sha256(prompt.encode()).hexdigest()
            item = cached.get((rid, cid))
            if item is not None:
                assert item['prompt_sha256'] == key
            else:
                item = dict(record_id=rid, chunk_id=cid, prompt_sha256=key, attempts=[], parsed=None)
                for attempt in range(2):
                    payload = dict(model='eboss-mistral', prompt=prompt + (FORMAT_RETRY_SUFFIX if attempt else ''),
                                   stream=False, options=SETTINGS)
                    trace = dict(request=payload, parsed=None)
                    try:
                        response = requests.post('http://localhost:11434/api/generate', json=payload, timeout=120)
                        response.raise_for_status()
                        data = response.json()
                        trace['response'] = {k: v for k, v in data.items() if k != 'context'}
                        value, error = parse_grounded_verdict(data['response'], context)
                        if data.get('done_reason') == 'length':
                            value, error = None, 'TRUNCATED'
                        trace.update(parsed=value, error=error)
                    except Exception as exc:
                        trace['error'] = str(exc)
                        item['attempts'].append(trace)
                        break  # A transport failure is not a format-retry opportunity.
                    item['attempts'].append(trace)
                    if trace['parsed'] is not None:
                        item['parsed'] = trace['parsed']
                        break
                item['status'] = 'SCORED' if item['parsed'] is not None else 'JUDGE_FAILURE'
                with result_file.open('a', encoding='utf-8') as handle:
                    handle.write(json.dumps(item, ensure_ascii=False, allow_nan=False) + '\n')
            verdicts[(rid, cid)] = item['parsed']
            progress = dict(completed=number, total=len(pairs), latest_record=rid, latest_chunk=cid,
                            latest_status=item['status'], elapsed_seconds=round(time.monotonic() - started, 1))
            write(OUT / 'progress.json', progress)
            log(f'{number}/{len(pairs)} {rid} {cid} {item["status"]}')
        comparisons = {name: aggregate(rows, records, verdicts, context_precision) for name, rows in grids.items()}
        all_results = [dict(tokenizer=name, **row) for name, rows in comparisons.items() for row in rows]
        complete = all(r['J'] is not None for r in all_results)
        best = max(all_results, key=lambda r: r['J']) if complete else None
        write(OUT / 'comparison.json', dict(results=comparisons, best=best,
              status='READY_FOR_REVIEW_NOT_FROZEN' if complete else 'INCOMPLETE_JUDGING_NO_SELECTION',
              held_out_accessed=False, freeze=False))
        import csv
        with (OUT / 'comparison_metrics.csv').open('w', encoding='utf-8', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=['tokenizer', 'grid_id', 'weights', 'k', 'J', 'failed_queries'])
            writer.writeheader()
            for row in all_results:
                writer.writerow({**{k: row[k] for k in ('tokenizer', 'grid_id', 'weights', 'k', 'J')},
                                 'failed_queries': len(row['failed_record_ids'])})
        assert all(sha(INPUTS[name]) == value for name, value in protocol['input_hashes'].items())
        log('Rescore finished. ' + ('Ready for review; not frozen.' if complete else 'Nulls remain; no final selection.'))
    finally:
        lock.unlink()


if __name__ == '__main__':
    main()
