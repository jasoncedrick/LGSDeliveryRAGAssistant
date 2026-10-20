"""Audit completed T07 judgments without repairing, retrying or imputing scores."""
import collections
import csv
import hashlib
import itertools
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.offline_judge_grounding import parse_grounded_verdict
from src.context_precision_judge_v2 import build_prompt


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def lines(path):
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')


def ap(values):
    running = numerator = 0.0
    for rank, value in enumerate(values, 1):
        running += value
        numerator += (running / rank) * value
    return numerator / (sum(values) + 1e-10)


def bounds(values):
    """Enumerate all binary completions; AP is not monotone in each verdict."""
    unknown = [i for i, value in enumerate(values) if value is None]
    possibilities = []
    for completion in itertools.product((0, 1), repeat=len(unknown)):
        complete = list(values)
        for i, value in zip(unknown, completion):
            complete[i] = value
        possibilities.append(ap(complete))
    return min(possibilities), max(possibilities)


def main():
    source = ROOT / 'experiments/t07-paired-grid-evaluator-v2'
    out = ROOT / 'experiments/t07-paired-grid-results-review-v1'
    assert not out.exists(), 'Preserve prior reviews; use a new version.'
    protocol = read(source / 'protocol.json')
    from scripts.rescore_t07_grids_v2 import INPUTS
    assert all(sha(INPUTS[name]) == value for name, value in protocol['input_hashes'].items())
    assert all(sha(ROOT / name) == value for name, value in protocol['implementation_hashes'].items())
    assert not (source / 'judge.lock').exists(), 'Do not review a running scorer.'
    judgments = lines(source / 'judge_verdicts.jsonl')
    records = {r['record_id']: r for r in lines(source / 'records.snapshot.jsonl')}
    chunks = {c['chunk_id']: c for c in read(INPUTS['corpus'])}
    pairs = {(r['record_id'], r['chunk_id']): r for r in judgments}
    assert len(judgments) == len(pairs) == protocol['unique_query_context_pairs'] == 1560
    verdicts = {}
    for key, result in pairs.items():
        rid, cid = key
        context = chunks[cid]['text_content']
        prompt = build_prompt(records[rid]['question'], records[rid]['reference_answer'], context)
        assert hashlib.sha256(prompt.encode()).hexdigest() == result['prompt_sha256']
        assert len(result['attempts']) in (1, 2)
        last = result['attempts'][-1]
        response = last.get('response')
        parsed = None
        if response and response.get('done_reason') != 'length':
            parsed, error = parse_grounded_verdict(response['response'], context)
        assert parsed == result['parsed'], 'Stored verdict disagrees with preserved raw response.'
        verdicts[key] = int(parsed['verdict']) if parsed else None
    failures = [r for r in judgments if r['parsed'] is None]
    use = collections.defaultdict(list)
    condition_bounds = []
    comparison = read(source / 'comparison.json')
    for tokenizer in ('original', 'punctuation'):
        rankings = [r for r in lines(source / (tokenizer + '.snapshot.jsonl')) if r['configuration'] == 'B']
        for grid in range(17):
            rows = [r for r in rankings if r['grid_id'] == grid]
            assert len(rows) == 90
            for k in (3, 5):
                cells = collections.defaultdict(list)
                failed_queries = []
                for row in rows:
                    rid = row['record_id']
                    ids = row['rankings'][str(k)]
                    values = [verdicts[(rid, cid)] for cid in ids]
                    low, high = bounds(values)
                    cells[records[rid]['pillar'] + '|' + records[rid]['language']].append((low, high))
                    if any(v is None for v in values):
                        failed_queries.append(rid)
                    for cid in ids:
                        if verdicts[(rid, cid)] is None:
                            use[(rid, cid)].append(dict(tokenizer=tokenizer, grid_id=grid, k=k))
                assert len(cells) == 15 and all(len(v) == 6 for v in cells.values())
                low = sum(sum(v[0] for v in values) / 6 for values in cells.values()) / 15
                high = sum(sum(v[1] for v in values) / 6 for values in cells.values()) / 15
                saved = next(r for r in comparison['results'][tokenizer] if r['grid_id'] == grid and r['k'] == k)
                assert saved['failed_record_ids'] == failed_queries
                assert (saved['J'] is None) == bool(failed_queries)
                condition_bounds.append(dict(tokenizer=tokenizer, grid_id=grid, weights=rows[0]['weights'],
                    k=k, failed_queries=len(failed_queries), J=saved['J'],
                    lower_bound=low, upper_bound=high))
    out.mkdir()
    packet = []
    for result in sorted(failures, key=lambda r: (-len(use[(r['record_id'], r['chunk_id'])]), r['record_id'], r['chunk_id'])):
        rid, cid = result['record_id'], result['chunk_id']
        chunk = chunks[cid]
        packet.append(dict(case_number=len(packet) + 1, record_id=rid, chunk_id=cid,
            question=records[rid]['question'], reference_answer=records[rid]['reference_answer'],
            actual_retrieved_context=chunk['text_content'],
            source_metadata={key: value for key, value in chunk.items() if key != 'text_content'},
            failure_type=result['attempts'][-1].get('error'),
            affected_conditions=use[(rid, cid)], attempts=result['attempts'],
            review_status='pending', source_comparison_notes='',
            review_policy='Supplemental review only. Do not replace archived RAGAS verdicts or call assistant notes independent human ratings.'))
    write(out / 'failed_judgments_review.json', packet)
    write(out / 'objective_bounds.json', dict(
        interpretation='Diagnostic bounds over every binary completion of missing verdicts, with existing valid verdicts fixed. These are not imputed scores, uncertainty intervals or confidence intervals. Remaining judge semantic errors are outside these bounds.',
        conditions=condition_bounds, selection_allowed=False))
    with (out / 'condition_coverage.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(condition_bounds[0]))
        writer.writeheader()
        writer.writerows(condition_bounds)
    summary = dict(total_pairs=len(judgments), valid=len(judgments) - len(failures), invalid=len(failures),
        invalid_fraction=len(failures) / len(judgments),
        failure_types=dict(collections.Counter(r['attempts'][-1].get('error') for r in failures)),
        affected_queries=len({r['record_id'] for r in failures}),
        affected_groups=len({records[r['record_id']]['question_group_id'] for r in failures}),
        failed_by_office_language=dict(collections.Counter(records[r['record_id']]['pillar'] + '|' + records[r['record_id']]['language'] for r in failures)),
        complete_conditions=sum(r['J'] is not None for r in condition_bounds), total_conditions=len(condition_bounds),
        bounded_dominating_candidates=[r for r in condition_bounds if all(r['lower_bound'] > other['upper_bound']
            for other in condition_bounds if other is not r)],
        status='EVALUATOR_OUTPUT_FAILURES_BLOCK_SELECTION', held_out_accessed=False, freeze=False,
        next_action='Review failed raw outputs against actual contexts; choose and predeclare a defensible evaluator protocol before new judging. No additional retries under the exhausted v2 policy.',
        methodology='20260923.pdf PDF33-34 and main Thesis Tracker T07; selection requires development Context Precision, then freeze before held-out A/B/C.',
        input_hashes={str(p.relative_to(ROOT)): sha(p) for p in [source / 'judge_verdicts.jsonl', source / 'comparison.json', source / 'protocol.json', INPUTS['references']]})
    write(out / 'summary.json', summary)
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
