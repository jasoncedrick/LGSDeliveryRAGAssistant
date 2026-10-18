"""Verify the completed 90-query archive and state the exact T06 validation scope."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.summarize_formal_development import main as summarize


def main(name):
    if Path(name).name!=name:raise ValueError('Use experiment directory name')
    directory=ROOT/'experiments'/name
    read=lambda p:json.loads(p.read_text(encoding='utf-8'))
    protocol=read(directory/'protocol.json')
    source_groups=ROOT/'experiments/t06-formal-development-validation-v2/development_groups.derived.json'
    assert hashlib.sha256(source_groups.read_bytes()).hexdigest()==protocol['source_groups_sha256']
    assert read(source_groups)==read(directory/'development_groups.snapshot.json')
    assert hashlib.sha256((directory/'normalization_prompt.txt').read_text(encoding='utf-8').encode()).hexdigest()==protocol['normalization_prompt_sha256']
    assert hashlib.sha256((ROOT/'data/municipal_dictionary_v1.json').read_bytes()).hexdigest()==protocol['artifact_hashes']['dictionary']
    rows=[json.loads(line) for line in (directory/'interactions.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(rows)==90 and len({r['record_id'] for r in rows})==90
    assert len({r['question_group_id'] for r in rows})==30
    for group in {r['question_group_id'] for r in rows}:
        assert {r['language'] for r in rows if r['question_group_id']==group}=={'english','taglish','bislish'}
    chunks={c['chunk_id']:c for c in read(ROOT/'experiments/chapter3-table-repaired-development-v1/corpus.json')}
    for row in rows:
        if row['citations']:
            assert len(row['citations'])==5 and len({c['chunk_id'] for c in row['citations']})==5
            for citation in row['citations']:
                assert citation['text']==chunks[citation['chunk_id']]['text_content']
            assert row['retrieved_rankings']['3']==row['retrieved_rankings']['5'][:3]
        if row['status'] in ('ANSWERED','GENERATION_INCOMPLETE','NO_SUPPORTED_ANSWER'):
            assert row['answer']==row['diagnostics']['raw_model_answer']
        if row['status']=='CLARIFICATION_REQUIRED':
            assert row['generation_started'] is False and not row['citations']
    identity=read(directory/'runtime_identity.json')
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha for p,sha in identity['source_code_sha256'].items())
    mapping=read(ROOT/'experiments/t06-formal-development-validation-v2/summary.json')
    assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha for p,sha in mapping['input_hashes'].items())
    provenance=read(ROOT/'experiments/chapter3-table-repaired-development-v1/index_provenance.json')
    assert all(hashlib.sha256((ROOT/'data/raw_charters'/p['file_source']).read_bytes()).hexdigest()==p['sha256']
               for p in provenance['source_pdfs'])
    summarize(name)
    metric_report=read(directory/'complete_outcome_summary/summary.json')
    report={'status':'T06_DEVELOPMENT_HARNESS_EXECUTION_VERIFIED_REFERENCE_VALIDATION_INCOMPLETE',
            'all_90_queries_processed':True,'groups':30,'languages':3,'generation_k':5,'retrieval_k':[3,5],
            'archive_context_text_matches_indexed_corpus':True,'all_generated_outputs_retained':True,
            'original_development_benchmark_unchanged':True,'source_artifacts_unchanged':True,
            'statuses':metric_report['statuses'],'provisional_metrics':metric_report['ranking_metrics'],
            'full_30_group_gold_validation_complete':False,'groups_requiring_source_reference_review':mapping['blocked_group_ids'],
            'source_review_queue':'experiments/t06-formal-development-validation-v2/source_review_queue.json',
            'ragas':'All four metric paths smoke-tested previously; this 90-query batch is archived for offline scoring, not yet RAGAS-scored.',
            'formal_results_ready':False,'held_out_accessed':False,'app_defaults_changed':False,
            'next_work':'Resolve the five source-reference mappings and semantically review references before reporting a full-cohort retrieval/RAGAS result. Current harness errors and low scores remain in archive.'}
    (directory/'completion_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    files=[p for p in directory.rglob('*') if p.is_file() and p.name not in ('hashes.json','final_hashes.json')]
    (directory/'final_hashes.json').write_text(json.dumps({str(p.relative_to(directory)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},indent=2),encoding='utf-8')
    print('Verified archive, original input hashes, all query variants and exact source context.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input-name',required=True);main(p.parse_args().input_name)
