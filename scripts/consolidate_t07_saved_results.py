"""Offline reconciliation of saved T07 development evidence; no final-test claims."""
import collections
import csv
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.development_retrieval_metrics import ranking_metrics

E = ROOT / 'experiments'
OUT = E / 't07-methodology-reconciliation-v1'
METRICS = ('faithfulness', 'context_precision', 'context_recall', 'answer_relevancy')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def lines(path):
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def export(path, rows):
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def summarize(values):
    valid = [v for v in values if v is not None]
    if any(not isinstance(v, (int, float)) or not math.isfinite(v) for v in valid):
        raise ValueError('Nonfinite saved value; do not silently coerce it.')
    return dict(mean=sum(valid) / len(valid) if valid else None, valid=len(valid), missing=len(values) - len(valid))


def main():
    assert not OUT.exists(), 'Preserve previous exports; use a new version.'
    reference_path = E / 't06-formal-development-validation-v4/methodology_and_tracker.json'
    reference = read(reference_path)
    assert reference['authoritative_tab'] == 'Thesis Tracker'
    assert sha(Path(reference['manuscript_path'])) == reference['manuscript_sha256']
    source = E / 't07-development-abc-v1'
    source_protocol = read(source / 'protocol.json')
    assert source_protocol['held_out_accessed'] is False and source_protocol['freeze'] is False
    paths = [reference_path, source / 'protocol.json']
    archives, scores = {}, {}
    for config in 'ABC':
        archive_path = source / config / 'interactions.jsonl'
        original_path = E / f't07-development-abc-ragas-{config.lower()}-v1/scores.json'
        retry_path = E / f't06-t07-development-closeout-v1/scores_{config}.with_retries.json'
        paths.extend([archive_path, original_path, retry_path])
        rows = lines(archive_path)
        assert len(rows) == len({r['record_id'] for r in rows}) == 90
        archives[config] = {r['record_id']: r for r in rows}
        scores[config] = {}
        for name, path in [('legacy_original', original_path), ('legacy_supplemental_retries', retry_path)]:
            rows = read(path)
            assert len(rows) == len({r['record_id'] for r in rows}) == 90
            scores[config][name] = {r['record_id']: r for r in rows}
            assert set(scores[config][name]) == set(archives[config])
    ids = set(archives['A'])
    assert all(set(archives[c]) == ids for c in 'ABC')
    assert len({r['question_group_id'] for r in archives['A'].values()}) == 30
    for rid in ids:
        assert len({archives[c][rid]['question'] for c in 'ABC'}) == 1
        assert len({archives[c][rid]['reference_answer'] for c in 'ABC'}) == 1
        assert all(archives[c][rid]['k'] == 3 for c in 'ABC')
    input_hashes = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    per_query, master, coverage = [], [], {}
    for config in 'ABC':
        rows = archives[config]
        coverage[config] = dict(collections.Counter(r['status'] for r in rows.values()))
        for rid, row in rows.items():
            recomputed = ranking_metrics(row['retrieved_rankings'].get('3', []), row['ground_truth_chunk_ids'], 3)
            assert recomputed == row['ranking_metrics'], 'Saved Hit/MRR differs from archived rankings/gold.'
            entry = dict(configuration=config, split='development', record_id=rid,
                generation_status=row['status'], k=3, hit_at_k=recomputed['hit_at_k'], mrr_at_k=recomputed['mrr_at_k'],
                context_sha256=hashlib.sha256(row['context'].encode()).hexdigest(),
                answer_sha256=hashlib.sha256(row['answer'].encode()).hexdigest(),
                known_case_flag='Unsupported local-fee-schedules claim accepted by retry judge' if config == 'B' and rid == 'SCENARIO-BFP-002-taglish' else '')
            for version, saved in scores[config].items():
                for metric in METRICS:
                    entry[version + '_' + metric] = saved[rid]['scores'].get(metric)
            per_query.append(entry)
        for metric in ('hit_at_k', 'mrr_at_k'):
            summary = summarize([r[metric] for r in per_query if r['configuration'] == config])
            master.append(dict(configuration=config, split='development', version='archived_retrieval', metric=metric,
                mean=summary['mean'], valid_queries=summary['valid'], eligible_missing=0, not_scored=0,
                all_queries=90, k=3, interpretation='All-query retrieval diagnostic; not the weight-selection objective.'))
        for version, saved in scores[config].items():
            for metric in METRICS:
                summary = summarize([r['scores'].get(metric) for r in saved.values()])
                skipped = sum(r['status'] == 'NOT_SCORED' for r in saved.values())
                master.append(dict(configuration=config, split='development', version=version, metric=metric,
                    mean=summary['mean'], valid_queries=summary['valid'], eligible_missing=summary['missing'] - skipped,
                    not_scored=skipped, all_queries=90, k=3,
                    interpretation='Mean on valid saved scores; unequal denominators, known judge errors, not final held-out evidence.'))
    OUT.mkdir()
    export(OUT / 'master_metrics.csv', master)
    export(OUT / 'all_query_records.csv', per_query)
    write(OUT / 'coverage.json', coverage)
    matched = E / 't06-t07-development-closeout-v1/matched_query_comparison.csv'
    (OUT / 'matched_complete_case_metrics.csv').write_bytes(matched.read_bytes())
    input_hashes[str(matched.relative_to(ROOT))] = sha(matched)
    write(OUT / 'provenance.json', dict(input_hashes=input_hashes, implementation_sha256=sha(Path(__file__)),
        source_protocol=source_protocol, original_scores_changed=False, new_model_calls=0,
        manual_reviews_required_by_this_export=0, held_out_accessed=False, freeze=False))
    write(OUT / 'completion_assessment.json', dict(
        T06='COMPLETE_IMPLEMENTATION_WITH_DOCUMENTED_EVALUATOR_LIMITATIONS',
        T07_development_execution_and_export='COMPLETE_WITH_DOCUMENTED_LIMITATIONS',
        T07_full_manuscript='INCOMPLETE_NO_REGISTERED_FREEZE_OR_HELD_OUT_ABC_RUN',
        saved_interactions=270, development_groups=30, queries_per_configuration=90,
        mandatory_duplicate_review=False, quote_perfection_is_manuscript_requirement=False,
        final_evaluation_required='Registered freeze followed by 70-group/210-query held-out A/B/C comparison; existing development outputs cannot replace it.',
        final_test_location='An old-project benchmark_scenarios_test.json filename exists; contents were not inspected or copied. No authoritative held-out manifest is registered in this clean project.',
        no_new_expensive_run=True, no_imputation=True, held_out_accessed=False, freeze=False,
        selection_status='Historical development selection preserved for provenance, not newly endorsed or frozen.',
        known_limitations=['Legacy judge accepts unsupported facts in at least the documented BFP case.',
            'V2 evidence-contract rescore has 110 missing judgments and no complete grid objective.',
            'Unsuccessful later evaluator experiments are retained, not blended into legacy scores.',
            'C removes query-specific dictionary injection while retaining shared static lexical guidance.',
            'Source ambiguity and incomplete generation outcomes remain documented.']))
    assert all(sha(ROOT / p) == value for p, value in input_hashes.items())
    print('Consolidated 270 unchanged development interactions, 30 aggregate rows; zero model calls. Full T07 is not falsely marked complete.')


if __name__ == '__main__':
    main()
