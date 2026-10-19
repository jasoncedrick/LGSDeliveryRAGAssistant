"""Register the historical development candidate before held-out preflight.

This entry point never rewrites benchmark answers/IDs and never calls generation.
An incompatible test benchmark must be reported, not silently treated as misses.
"""
import collections
import datetime
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'experiments/t07-final-evaluation-v1'
TEST = Path('D:/thesis/LGSDeliveryRAGAssistant-main/data/benchmark_scenarios_test.json')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def check_groups(groups, corpus_ids, development_ids):
    """Structural/ID checks only; do not infer replacement relevance labels."""
    errors = []
    if not isinstance(groups, list):
        return dict(ready=False, errors=['BENCHMARK_NOT_GROUP_LIST'])
    if len(groups) != 70:
        errors.append('EXPECTED_70_GROUPS')
    ids = [g.get('group_id') for g in groups]
    if len(set(ids)) != len(ids) or None in ids:
        errors.append('INVALID_OR_DUPLICATE_GROUP_IDS')
    if set(ids) & development_ids:
        errors.append('DEVELOPMENT_TEST_GROUP_OVERLAP')
    missing = {}
    pillars = collections.Counter()
    query_count = 0
    for g in groups:
        gid = g.get('group_id', '<missing>')
        pillars[g.get('pillar')] += 1
        if g.get('split') not in ('test', 'held_out', 'held-out'):
            errors.append('WRONG_SPLIT:' + str(gid))
        queries = g.get('queries', {})
        if not isinstance(queries, dict) or set(queries) != {'english', 'taglish', 'bislish'} or not all(isinstance(q, str) and q.strip() for q in queries.values()):
            errors.append('INVALID_LANGUAGE_VARIANTS:' + str(gid))
        else:
            query_count += 3
        gold = g.get('ground_truth_chunk_ids')
        if not isinstance(gold, list) or not gold or any(not isinstance(cid, str) for cid in gold):
            errors.append('MISSING_OR_INVALID_GOLD_IDS:' + str(gid))
        else:
            absent = [cid for cid in gold if cid not in corpus_ids]
            if absent:
                missing[gid] = absent
        if not isinstance(g.get('ground_truth_reference_answer'), str) or not g['ground_truth_reference_answer'].strip():
            errors.append('MISSING_REFERENCE:' + str(gid))
    if len(pillars) != 5 or set(pillars.values()) != {14}:
        errors.append('EXPECTED_14_GROUPS_PER_OFFICE')
    if query_count != 210:
        errors.append('EXPECTED_210_QUERIES')
    if missing:
        errors.append('GOLD_IDS_NOT_IN_FROZEN_CORPUS')
    return dict(ready=not errors, errors=errors, group_count=len(groups), query_count=query_count,
        groups_per_office=dict(pillars), missing_gold_ids=missing,
        affected_groups=len(missing), unique_missing_gold_ids=len({cid for values in missing.values() for cid in values}))


def main():
    import requests
    refs = read(ROOT / 'experiments/t06-formal-development-validation-v4/methodology_and_tracker.json')
    assert sha(Path(refs['manuscript_path'])) == refs['manuscript_sha256']
    assert refs['authoritative_tab'] == 'Thesis Tracker'
    grid_path = ROOT / 'experiments/t07-development-grid-format-retry-v2/context_precision_grid.json'
    grid = read(grid_path)
    best = grid['best_complete_candidate']
    weights = read(grid_path.parent / 'protocol.json')['weight_grid'][best['grid_id']]
    assert grid['selection_status'] == 'READY_FOR_COMPARISON_NOT_FROZEN'
    assert all(r['J'] is not None for r in grid['results'])
    assert weights == [0.75, 0.25, 0.0] and best['k'] == 3
    corpus_dir = ROOT / 'experiments/chapter3-table-repaired-development-v1'
    validation = read(corpus_dir / 'validation.json')
    assert validation['passed'] and validation['window_tokens'] == 120 and validation['overlap_tokens'] == 20
    corpus = read(corpus_dir / 'corpus.json')
    development = read(ROOT / 'data/benchmark_scenarios_dev.json')
    assert len(development) == 30
    tags = requests.get('http://localhost:11434/api/tags', timeout=10).json()['models']
    model = next(m for m in tags if m['name'] == 'eboss-mistral:latest')
    assert model['digest'] == read(ROOT / 'experiments/t07-development-abc-v1/protocol.json')['model_digest']
    # Do not read TEST until the registration and its seal have been written.
    paths = [p for folder in ('app', 'src', 'config') for p in (ROOT / folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.py', '.json', '.txt')]
    paths += [p for p in corpus_dir.iterdir() if p.is_file()]
    paths += [ROOT / 'data/municipal_dictionary_v1.json', grid_path, grid_path.parent / 'protocol.json', Path(__file__), ROOT / 'scripts/score_development_ragas.py', ROOT / 'scripts/run_t07_development_abc.py', ROOT / 'data/benchmark_scenarios_dev.json']
    packages = {}
    for name in ('ragas', 'torch', 'transformers', 'sentence-transformers', 'rank-bm25', 'faiss-cpu', 'langchain-community'):
        packages[name] = importlib.metadata.version(name)
    assert not OUT.exists(), 'Preserve existing registration; do not silently register another test run.'
    OUT.mkdir()
    registration = dict(status='REGISTERED_CANDIDATE_BEFORE_HELD_OUT_PREFLIGHT',
        registered_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        selection_basis='Historical completed development grid, not later incomplete evaluator experiments.',
        historical_J=best['J'], grid_id=best['grid_id'], weights_B_C=weights, k=3,
        tokenizer='Existing whitespace BM25 tokenizer, unchanged',
        model='eboss-mistral', model_digest=model['digest'], packages=packages,
        normalizer_settings=dict(num_predict=150, temperature=0, top_p=0),
        generation_settings=dict(num_ctx=8192, num_predict=1536, temperature=0, top_p=0),
        evaluator='Existing RAGAS 0.1.5 legacy output-contract-v1, identical across A/B/C. Failures remain null; no quote-perfectness gate or new evaluator experiments.',
        evaluator_settings=dict(num_ctx=8192, num_predict=4096, temperature=0, top_p=0, timeout=600, max_workers=1, max_retries=0),
        configurations=dict(A='Raw query BM25 only, same generator/prompt.',
            B='Query-specific dictionary injection, normalization, chunk-level hybrid retrieval.',
            C='Same as B with query-specific dictionary injection disabled; identical ambiguity gate and retrieval boost. Shared static prompt guidance remains.'),
        known_limitations=['Legacy judge semantic errors documented; numbers are automated judgments, not validated factual truth.',
            'Floating-point near tie in historical grid; no meaningful superiority claim.',
            'Shared static lexical prompt guidance retained in C.',
            'Existing source ambiguity and incomplete-generation risk retained.',
            'Current answer prompt includes inline citation format guidance; not asserted to fully implement the manuscript wording about two complete examples.'],
        held_out_path=str(TEST), held_out_contents_inspected_before_registration=False,
        preflight_policy='After registration, validate 70 groups, no group overlap, 210 queries, 14 groups per office, gold IDs present. No rewriting test IDs/reference answers. Stop before inference if incompatible.',
        manuscript_sha256=refs['manuscript_sha256'], authoritative_tracker_tab='Thesis Tracker',
        file_hashes={str(p.relative_to(ROOT)): sha(p) for p in sorted(set(paths))},
        app_defaults_changed=False)
    write(OUT / 'candidate_registration.json', registration)
    write(OUT / 'registration_seal.json', dict(candidate_registration_sha256=sha(OUT / 'candidate_registration.json')))
    assert all(sha(ROOT / p) == value for p, value in registration['file_hashes'].items())
    groups = read(TEST)
    test_hash = sha(TEST)
    result = check_groups(groups, {c['chunk_id'] for c in corpus}, {g['group_id'] for g in development})
    result.update(test_sha256=test_hash, test_path=str(TEST), held_out_structure_accessed=True,
                  query_text_output_to_console=False, test_contents_changed=False,
                  new_model_inference_calls=0,
                  final_status='PREFLIGHT_PASSED_AWAITING_SINGLE_PASS_EXECUTION' if result['ready'] else 'PREFLIGHT_BLOCKED_NO_FINAL_INFERENCE')
    write(OUT / 'preflight.json', result)
    assert sha(TEST) == test_hash
    print(json.dumps({k: v for k, v in result.items() if k != 'missing_gold_ids'}, indent=2))


if __name__ == '__main__':
    main()
