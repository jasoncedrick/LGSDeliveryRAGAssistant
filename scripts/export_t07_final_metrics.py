"""Export every final outcome, null and denominator; never invent missing scores."""
import collections
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'experiments/t07-final-evaluation-v1'
METRICS = ('hit_at_k', 'mrr_at_k', 'faithfulness', 'context_precision', 'context_recall', 'answer_relevancy')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def rows(path):
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()] if path.exists() else []


def mean(values):
    finite = [v for v in values if isinstance(v, (int, float)) and math.isfinite(v)]
    return sum(finite) / len(finite) if finite else None, len(finite)


def csv_write(path, data):
    temp = path.with_name(path.name + '.tmp')
    with temp.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(data[0]))
        writer.writeheader()
        writer.writerows(data)
    temp.replace(path)


def main():
    all_rows, summaries, coverage, maps = [], [], {}, {}
    scores_complete = True
    for config in 'ABC':
        archives = rows(OUT / config / 'interactions.jsonl')
        score_path = ROOT / 'experiments' / f't07-final-ragas-{config.lower()}-v1/scores.json'
        scores = {r['record_id']: r for r in read(score_path)} if score_path.exists() else {}
        scores_complete &= len(scores) == 210
        maps[config] = {}
        for r in archives:
            record = dict(configuration=config, split='held_out_test', record_id=r['record_id'],
                group_id=r['question_group_id'], office=r['pillar'], language=r['language'],
                generation_status=r['status'], label_status=r['relevance_mapping_status'],
                judge_status=scores.get(r['record_id'], {}).get('status', 'PENDING'), k=3)
            record.update(r['ranking_metrics'])
            record.update({m: scores.get(r['record_id'], {}).get('scores', {}).get(m) for m in METRICS[2:]})
            maps[config][r['record_id']] = record
            all_rows.append(record)
        coverage[config] = dict(archived=len(archives), planned=210,
            statuses=dict(collections.Counter(r['status'] for r in archives)),
            complete_relevance_labels=sum(r['relevance_mapping_status'] == 'COMPLETE_SOURCE_SPAN_TRANSFER' for r in archives),
            judge_records=len(scores))
        for metric in METRICS:
            records = list(maps[config].values())
            value, valid = mean([r[metric] for r in records])
            summaries.append(dict(configuration=config, split='held_out_test', metric=metric, mean_on_valid_scores=value,
                valid_queries=valid, archived_queries=len(records), planned_queries=210,
                missing_or_skipped=len(records) - valid, k=3,
                interpretation='Source-span-transferred relevance; incomplete labels null. Automated judge errors/skip outcomes retained; not independent expert certification.'))
    if not all_rows:
        raise ValueError('No final outcomes yet; do not create empty final results.')
    csv_write(OUT / 'master_metrics.csv', summaries)
    csv_write(OUT / 'per_query_metrics.csv', all_rows)
    paired = []
    for metric in METRICS:
        ids = set(maps['A']) & set(maps['B']) & set(maps['C'])
        common = [rid for rid in sorted(ids) if all(isinstance(maps[c][rid][metric], (int, float)) and math.isfinite(maps[c][rid][metric]) for c in 'ABC')]
        values = {c: mean([maps[c][rid][metric] for rid in common])[0] for c in 'ABC'}
        paired.append(dict(metric=metric, matched_queries=len(common), **values,
            B_minus_A=values['B'] - values['A'] if common else None,
            B_minus_C=values['B'] - values['C'] if common else None,
            interpretation='Shared complete cases, descriptive only; not all-query effectiveness or a significance test.'))
    csv_write(OUT / 'matched_metrics.csv', paired)
    generation_complete = all(v['archived'] == 210 for v in coverage.values())
    complete = generation_complete and scores_complete
    assessment = dict(status='EXECUTION_AND_CSV_EXPORT_COMPLETE_WITH_MISSING_METRICS' if complete else 'RUNNING_NOT_FINAL',
        planned_interactions=630, archived_interactions=len(all_rows), coverage=coverage,
        generation_complete=generation_complete, scoring_attempts_complete=scores_complete,
        all_metrics_fully_observed=all(r['valid_queries'] == 210 for r in summaries),
        source_label_limit='77/87 legacy spans transferred; 59/70 groups complete. Incomplete groups are not scored as retrieval misses and are retained for generation/reference-based RAGAS.',
        reference_limit='Original held-out references retained, not independently corrected or certified.',
        evaluator_limit='Legacy local Mistral judge has known semantic/format errors; no final-test prompt tuning, score overrides or hidden retries.',
        protocol_limit='Span-transfer addendum registered after structural preflight and before model outcomes. Source-window intersections can broaden relevance at boundaries; report this distinction from original chunk IDs.',
        held_out_accessed=True, original_benchmark_changed=False, test_driven_tuning=False)
    (OUT / 'completion_assessment.json').write_text(json.dumps(assessment, indent=2), encoding='utf-8')
    if complete:
        (OUT / 'T07_EXECUTION_REPORT.txt').write_text(
            'T07 FINAL A/B/C EXECUTION AND CSV EXPORT COMPLETE WITH DOCUMENTED LIMITATIONS\n\n'
            'All 630 held-out query/configuration outcomes are archived. Each of 210 queries was retained for A, B and C. '
            'Offline RAGAS scoring was attempted once for every eligible answer; clarification, incomplete generation, judge failures and interruptions remain explicit.\n\n'
            'master_metrics.csv contains all metric-specific denominators. per_query_metrics.csv retains every outcome; matched_metrics.csv is a shared complete-case descriptive comparison.\n\n'
            'Gold coverage is incomplete: 77/87 legacy source spans were identity-transferred, covering 59/70 complete groups (177/210 query variants). '
            'The other 11 groups remain in the run with Hit/MRR null. This is execution/export completion, not complete retrieval-label coverage or independent factual certification. '
            'Boundary-overlap transfer can broaden relevance; original references and known judge limitations are preserved.\n\n'
            'Settings: historical development-selected whitespace BM25, weights .75/.25/0, K3, same Mistral generator and legacy offline evaluator for A/B/C. '
            'No model/prompt/weight changes or regeneration were made from test outcomes. Original benchmark hash, candidate registration and execution addendum are archived.\n\n'
            'Methodology: 20260923.pdf Chapter3 PDF28,30,32-34; main Thesis Tracker T07. Human employee auditing remains separate.\n', encoding='utf-8')
    print(f'CSV refreshed: {len(all_rows)}/630 generation outcomes; scoring_complete={scores_complete}; execution_complete={complete}', flush=True)


if __name__ == '__main__':
    main()
