"""Registered single-pass held-out A/B/C generation with explicit label gaps."""
import argparse
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'experiments/t07-final-evaluation-v1'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    tmp.replace(path)


def load_registered():
    candidate = read(OUT / 'candidate_registration.json')
    assert sha(OUT / 'candidate_registration.json') == read(OUT / 'registration_seal.json')['candidate_registration_sha256']
    assert all(sha(ROOT / name) == value for name, value in candidate['file_hashes'].items())
    crosswalk = read(OUT / 'source_span_crosswalk.json')
    assert sha(OUT / 'source_span_crosswalk.json') == read(OUT / 'source_span_crosswalk.seal.json')['sha256']
    assert all(sha(Path(name)) == value for name, value in crosswalk['inputs'].items())
    test = Path(candidate['held_out_path'])
    groups = read(test)
    development = read(ROOT / 'data/benchmark_scenarios_dev.json')
    assert len(groups) == len({g['group_id'] for g in groups}) == 70
    assert not ({g['group_id'] for g in groups} & {g['group_id'] for g in development})
    assert all(g['split'] == 'held_out_test' and set(g['queries']) == {'english', 'taglish', 'bislish'} for g in groups)
    assert set(crosswalk['groups']) == {g['group_id'] for g in groups}
    manifest = dict(
        registered_before_inference_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        candidate_registration_sha256=sha(OUT / 'candidate_registration.json'),
        source_crosswalk_sha256=sha(OUT / 'source_span_crosswalk.json'), benchmark_sha256=sha(test),
        execution_code_hashes={name: sha(ROOT / name) for name in (
            'scripts/run_t07_final_abc.py', 'scripts/run_t07_final_workflow.py',
            'scripts/score_final_ragas.py', 'scripts/export_t07_final_metrics.py',
            'scripts/align_t07_source_spans.py', 'scripts/build_t07_final_scorer.py')},
        configurations=['A', 'B', 'C'], groups=70, queries_per_configuration=210, planned_interactions=630,
        k=3, weights_B_C=[0.75, 0.25, 0.0], frozen=True,
        evaluator_flags=['--strict-metric-json', '--strict-recall-json'],
        original_benchmark_unchanged=True, held_out_accessed=True,
        label_policy='Source-span crosswalk only, registered before outcomes. Incomplete groups keep all queries but Hit/MRR null. Report source-overlap relevance transfer and denominators; no claims of complete gold coverage.',
        coverage=dict(complete_groups=sum(g['complete'] for g in crosswalk['groups'].values()), total_groups=70),
        resume_policy='Never regenerate a recorded outcome. An interrupted in-flight attempt is archived as interrupted rather than retried. Judge outputs use the same single-pass policy.',
        protocol_amendment='Evaluation adapter and source-span ID transfer registered after structural test preflight but before any model outcomes. Generation/retrieval model, prompts, weights, K and corpus unchanged. No test-driven tuning.')
    path = OUT / 'execution_manifest.json'
    if path.exists():
        old = read(path)
        manifest['registered_before_inference_utc'] = old['registered_before_inference_utc']
        assert old == manifest
        assert sha(path) == read(OUT / 'execution_manifest.seal.json')['sha256']
    else:
        write(path, manifest)
        write(OUT / 'execution_manifest.seal.json', dict(sha256=sha(path)))
    return candidate, crosswalk, groups, manifest


def main(prepare_only=False):
    candidate, crosswalk, groups, manifest = load_registered()
    if prepare_only:
        print('Execution registration verified: 70 groups, 630 planned outcomes, source-label coverage=' + str(manifest['coverage']))
        return
    import numpy as np
    import requests
    from app.pipeline import Pipeline
    from scripts.run_t07_development_abc import InjectionDisabledNormalizer, sparse_retrieval
    from src.development_retrieval_metrics import ranking_metrics
    models = requests.get('http://localhost:11434/api/tags', timeout=10).json()['models']
    assert next(m for m in models if m['name'] == 'eboss-mistral:latest')['digest'] == candidate['model_digest']
    fd = os.open(OUT / 'generation.lock', os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    def log(message):
        print(message, flush=True)
        with (OUT / 'console.log').open('a', encoding='utf-8') as handle:
            handle.write(message + '\n')
    try:
        pipeline = Pipeline(artifacts_dir=ROOT / 'experiments/chapter3-table-repaired-development-v1')
        assert pipeline.model_name == 'eboss-mistral' and pipeline.num_ctx == 8192 and pipeline.answer_tokens == 1536
        pipeline.retriever.weights = np.asarray(candidate['weights_B_C'])
        c_normalizer = InjectionDisabledNormalizer(str(ROOT / 'data/municipal_dictionary_v1.json'), enable_context_rules=False)
        prompt = (ROOT / 'config/normalization_intent_candidate.txt').read_text(encoding='utf-8')
        completed = {}
        for config in 'ABC':
            folder = OUT / config
            folder.mkdir(exist_ok=True)
            protocol = dict(held_out_accessed=True, freeze=True, configuration=config, k=3,
                weights_B_C=candidate['weights_B_C'], execution_manifest_sha256=sha(OUT / 'execution_manifest.json'),
                reference_policy='Original held-out reference unchanged; no outcome-driven corrections.',
                label_policy=manifest['label_policy'])
            if (folder / 'protocol.json').exists():
                assert read(folder / 'protocol.json') == protocol
            else:
                write(folder / 'protocol.json', protocol)
            path = folder / 'interactions.jsonl'
            completed[config] = [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines()] if path.exists() else []
        done = {(c, r['record_id']) for c, rows in completed.items() for r in rows}
        def save(config, row):
            with (OUT / config / 'interactions.jsonl').open('a', encoding='utf-8') as handle:
                handle.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + '\n')
            completed[config].append(row)
            done.add((config, row['record_id']))
            write(OUT / 'generation_progress.json', dict(completed=sum(len(v) for v in completed.values()), total=630,
                by_configuration={c: len(v) for c, v in completed.items()}, latest=dict(configuration=config, record_id=row['record_id'], status=row['status'])))
            log(f'{sum(len(v) for v in completed.values())}/630 {config} {row["record_id"]} {row["status"]}')
        # An interrupted attempt remains unfavorable evidence, not a hidden retry.
        inflight = OUT / 'inflight_interaction.json'
        if inflight.exists():
            prior = read(inflight)
            row, config = prior['record'], prior['configuration']
            if (config, row['record_id']) not in done:
                row.update(status='INTERRUPTED_PIPELINE', error='Attempt interrupted; no automatic model retry.', ranking_metrics={'hit_at_k': None, 'mrr_at_k': None})
                save(config, row)
            inflight.unlink()
        for group in groups:
            mapping = crosswalk['groups'][group['group_id']]
            for language in ('english', 'taglish', 'bislish'):
                rid = group['group_id'] + '-' + language
                for config in 'ABC':
                    if (config, rid) in done:
                        continue
                    row = dict(record_id=rid, question_id=rid, question_group_id=group['group_id'],
                        split='held_out_test', language=language, question=group['queries'][language], pillar=group['pillar'],
                        reference_answer=group['ground_truth_reference_answer'], reference_status='ORIGINAL_HELD_OUT_REFERENCE_UNCHANGED',
                        original_ground_truth_chunk_ids=group['ground_truth_chunk_ids'], ground_truth_chunk_ids=mapping['mapped_ids'],
                        relevance_mapping_status='COMPLETE_SOURCE_SPAN_TRANSFER' if mapping['complete'] else 'INCOMPLETE_SOURCE_SPAN_TRANSFER',
                        unresolved_legacy_ids=mapping['unresolved_ids'], configuration=config, k=3,
                        citations=[], context='', answer='', status='PENDING', retrieved_rankings={}, generation_started=False)
                    write(inflight, dict(configuration=config, record=row))
                    try:
                        if config == 'A':
                            normalization = dict(status='BYPASSED', normalized_query=row['question'])
                            retrieval = sparse_retrieval(pipeline.retriever, row['question'], 3)
                        else:
                            normalizer = pipeline.normalizer if config == 'B' else c_normalizer
                            with patch('src.query_normalizer.BASELINE_SYSTEM_PROMPT', prompt):
                                normalization = normalizer.normalize(row['question'])
                            retrieval = None
                            if normalization['status'] == 'FALLBACK_TRIGGERED':
                                row.update(status='CLARIFICATION_REQUIRED', answer=normalization.get('clarification_prompt') or '')
                            elif normalization['status'] != 'SUCCESS' or not normalization.get('normalized_query'):
                                row['status'] = 'NORMALIZATION_ERROR'
                            else:
                                retrieval = pipeline.retriever.retrieve(normalization['normalized_query'], top_k=3)
                        row['normalization'] = normalization
                        if retrieval:
                            row.update(search_query=normalization['normalized_query'], citations=retrieval['citations'],
                                context=retrieval['context'], retrieved_rankings={'3': retrieval['source_chunk_ids']})
                            write(inflight, dict(configuration=config, record=row))
                            row.update(pipeline._generate_answer(row['question'], retrieval))
                    except Exception as exc:
                        row.update(status='PIPELINE_ERROR', error=str(exc))
                    row['ranking_metrics'] = ranking_metrics(row['retrieved_rankings'].get('3', []), mapping['mapped_ids'], 3) if mapping['complete'] else {'hit_at_k': None, 'mrr_at_k': None}
                    save(config, row)
                    inflight.unlink()
        assert all(len(rows) == len({r['record_id'] for r in rows}) == 210 for rows in completed.values())
        for config in 'ABC':
            write(OUT / config / 'archive_seal.json', dict(sha256=sha(OUT / config / 'interactions.jsonl')))
        assert all(sha(ROOT / path) == value for path, value in candidate['file_hashes'].items())
        log('All 630 generation outcomes archived and sealed. Offline RAGAS next; no tuning or regeneration.')
    finally:
        (OUT / 'generation.lock').unlink()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare-only', action='store_true')
    main(parser.parse_args().prepare_only)
