"""Batch the 30 development groups through current chunk RAG, preserving all outcomes."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.development_retrieval_metrics import ranking_metrics


def load_development_groups(path):
    groups=json.loads(path.read_text(encoding='utf-8'))
    if len(groups)!=30 or len({g['group_id'] for g in groups})!=30:
        raise ValueError('Require 30 unique development groups')
    if any(g.get('split')!='development' or set(g['queries'])!={'english','taglish','bislish'} for g in groups):
        raise ValueError('Require development-only groups with three language variants')
    return groups


def reference_metadata(groups):
    return {'mapped_groups':sum(bool(g['ground_truth_chunk_ids']) for g in groups),
            'mapping_status_counts':dict(Counter(g['mapping_status'] for g in groups)),
            'reference_policy':'Score available relevance labels; preserve mapping status. Missing retrieval counts as zero when labels exist. Unmapped labels remain unscored.',
            'source_reference_answer_status':'Mixed development provenance; assistant source review is not independent expert certification.'}


def score_record(record):
    return {str(k): ranking_metrics(record['retrieved_rankings'].get(str(k),[]),record['ground_truth_chunk_ids'],k)
            if record['ground_truth_chunk_ids'] else {'status':'WITHHELD_UNMAPPED_REFERENCES'} for k in (3,5)}


def main(args):
    import torch
    from app.pipeline import Pipeline,ANSWER_SYSTEM_PROMPT
    from src.query_normalizer import BASELINE_SYSTEM_PROMPT
    reference_file=args.references if args.references.is_absolute() else ROOT/args.references
    artifact_dir=ROOT/'experiments/chapter3-table-repaired-development-v1'
    output=ROOT/'experiments'/args.output_name
    if Path(args.output_name).name!=args.output_name or output.exists():raise ValueError('Use a new experiment name')
    read=lambda p:json.loads(p.read_text(encoding='utf-8'))
    groups=load_development_groups(reference_file)
    assert len(groups)==30 and all(g['split']=='development' for g in groups)
    prompt=Path(args.prompt_file).read_text(encoding='utf-8') if args.prompt_file else BASELINE_SYSTEM_PROMPT
    pipeline=Pipeline(artifacts_dir=artifact_dir)
    output.mkdir()
    write=lambda name,value:(output/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    write('development_groups.snapshot.json',groups)
    (output/'normalization_prompt.txt').write_text(prompt,encoding='utf-8')
    write('protocol.json',{'status':'DEVELOPMENT_ONLY_UNFROZEN_CANDIDATE','groups':30,'queries':90,'retrieval_k':[3,5],
          'generation_k':5,'candidate_prompt':str(args.prompt_file) if args.prompt_file else None,
          'normalization_prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
          'answer_prompt_sha256':hashlib.sha256(ANSWER_SYSTEM_PROMPT.encode()).hexdigest(),
          'artifact_hashes':pipeline.retriever.artifact_hashes,'source_groups_sha256':digest(reference_file),
          'reference_file':str(reference_file), **reference_metadata(groups),
          'held_out_accessed':False,'app_defaults_changed':False,'freeze':False})
    all_records=[]
    for group in groups:
        for language,query in group['queries'].items():
            record={'record_id':group['group_id']+'-'+language,'question_id':group['group_id']+'-'+language,
                    'question_group_id':group['group_id'],'language':language,'question':query,'pillar':group['pillar'],
                    'created_utc':datetime.now(timezone.utc).isoformat(),'k':5,
                    'reference_answer':group['ground_truth_reference_answer'],'reference_status':group['mapping_status'],
                    'relevance_mapping_status':group['mapping_status'],'ground_truth_chunk_ids':group['ground_truth_chunk_ids'],
                    'citations':[],'retrieved_rankings':{},'ranking_metrics':{},'answer':'','generation_started':False}
            try:
                with patch('src.query_normalizer.BASELINE_SYSTEM_PROMPT',prompt):
                    normalization=pipeline.normalizer.normalize(query)
                record['normalization']=normalization
                normalized=normalization.get('normalized_query')
                if normalization['status']=='FALLBACK_TRIGGERED':
                    record.update(status='CLARIFICATION_REQUIRED',clarification_prompt=normalization.get('clarification_prompt'),answer=normalization.get('clarification_prompt') or '')
                elif normalization['status']!='SUCCESS' or not normalized:
                    record.update(status='NORMALIZATION_ERROR',error='No usable normalized query')
                else:
                    record['search_query']=normalized
                    retrieved=pipeline.retriever.retrieve(normalized,top_k=5)
                    for k in (3,5):
                        ids=retrieved['source_chunk_ids'][:k]
                        record['retrieved_rankings'][str(k)]=ids
                        if group['ground_truth_chunk_ids']:
                            record['ranking_metrics'][str(k)]=ranking_metrics(ids,group['ground_truth_chunk_ids'],k)
                        else:record['ranking_metrics'][str(k)]={'status':'WITHHELD_UNMAPPED_REFERENCES'}
                    record.update(context=retrieved['context'],citations=retrieved['citations'])
                    record.update(pipeline._generate_answer(query,retrieved))
            except Exception as error:
                record.update(status='PIPELINE_ERROR',error_type=type(error).__name__,error=str(error))
            record['ranking_metrics']=score_record(record)
            with (output/'interactions.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
            all_records.append(record)
            write('progress.json',{'processed':len(all_records),'expected':90,'statuses':dict(Counter(r['status'] for r in all_records))})
            print(f"{len(all_records)}/90 {record['record_id']} {record['status']}",flush=True)
    assert len(all_records)==90 and len({r['record_id'] for r in all_records})==90
    import csv
    with (output/'metrics.csv').open('w',newline='',encoding='utf-8') as f:
        fields=['group_id','language','status','mapping_status','k','hit_at_k','mrr_at_k','metric_status']
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for record in all_records:
            for k in (3,5):
                metric=record['ranking_metrics'].get(str(k),{})
                writer.writerow({'group_id':record['question_group_id'],'language':record['language'],'status':record['status'],
                                 'mapping_status':record['relevance_mapping_status'],'k':k,'hit_at_k':metric.get('hit_at_k'),
                                 'mrr_at_k':metric.get('mrr_at_k'),'metric_status':metric.get('status','PROVISIONAL_SCORED' if metric else 'NOT_RETRIEVED')})
    summaries=[]
    for k in (3,5):
        scored=[r['ranking_metrics'][str(k)] for r in all_records if 'hit_at_k' in r['ranking_metrics'].get(str(k),{})]
        summaries.append({'k':k,'queries_with_ranking_scores':len(scored),'hit_at_k':sum(x['hit_at_k'] for x in scored)/len(scored) if scored else None,
                          'mrr_at_k':sum(x['mrr_at_k'] for x in scored)/len(scored) if scored else None})
    write('summary.json',{'status':'BATCH_FINISHED_DEVELOPMENT_ONLY','processed':90,'statuses':dict(Counter(r['status'] for r in all_records)),
          'provisional_ranking_metrics':summaries,'excluded_from_ranking':'Only groups with missing relevance labels. Stopped queries with labels count as zero.',
          'not_full_90_query_metric':any(not g['ground_truth_chunk_ids'] for g in groups),'all_outputs_retained':True,'offline_ragas_status':'pending for this batch',
          'held_out_accessed':False,'app_defaults_changed':False})
    write('hashes.json',{p.name:digest(p) for p in output.iterdir() if p.is_file()})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-name',required=True);p.add_argument('--prompt-file',type=Path)
    p.add_argument('--references',type=Path,default=Path('experiments/t06-formal-development-validation-v3/development_groups.derived.json'))
    main(p.parse_args())
