"""Summarize all 90 outcomes; stopped queries count as misses when relevance is mapped."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.development_retrieval_metrics import ranking_metrics


def main(name):
    if Path(name).name!=name:raise ValueError('Use experiment directory name')
    source=ROOT/'experiments'/name
    output=source/'complete_outcome_summary'
    if output.exists():raise ValueError('Keep prior summary')
    records=[json.loads(line) for line in (source/'interactions.jsonl').read_text(encoding='utf-8').splitlines()]
    if len(records)!=90 or len({r['record_id'] for r in records})!=90:raise ValueError('Wait for all 90 unique outcomes')
    groups=json.loads((source/'development_groups.snapshot.json').read_text(encoding='utf-8'))
    assert {r['question_group_id'] for r in records}=={g['group_id'] for g in groups}
    rows=[]
    for record in records:
        gold=record['ground_truth_chunk_ids']
        for k in (3,5):
            ids=record['retrieved_rankings'].get(str(k),[])
            metric=ranking_metrics(ids,gold,k) if gold else {'hit_at_k':None,'mrr_at_k':None}
            rows.append({'record_id':record['record_id'],'group_id':record['question_group_id'],'pillar':record['pillar'],
                         'language':record['language'],'k':k,'pipeline_status':record['status'],
                         'ranking_status':'PROVISIONAL_SCORED' if gold else 'WITHHELD_UNMAPPED_REFERENCE',**metric})
    summary=[]
    for k in (3,5):
        eligible=[r for r in rows if r['k']==k and r['hit_at_k'] is not None]
        summary.append({'k':k,'denominator':len(eligible),'all_mapped_queries_included':True,
                        'hit_at_k':sum(r['hit_at_k'] for r in eligible)/len(eligible),
                        'mrr_at_k':sum(r['mrr_at_k'] for r in eligible)/len(eligible),
                        'by_language':{language:{'queries':sum(r['language']==language for r in eligible),
                           'hits':sum(r['hit_at_k'] for r in eligible if r['language']==language)} for language in ['english','taglish','bislish']}})
    output.mkdir()
    with (output/'per_query_metrics.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    report={'status':'COMPLETE_OUTCOME_ACCOUNTING_WITH_PROVISIONAL_LABELS','records':90,'groups':30,
            'statuses':dict(Counter(r['status'] for r in records)),'ranking_metrics':summary,
            'unmapped_groups':[g['group_id'] for g in groups if not g['ground_truth_chunk_ids']],
            'policy':'Clarification, normalization errors, retrieval errors and generation errors remain in archive. For mapped groups, missing retrieval counts as zero Hit/MRR. No fabricated gold for unmapped groups.',
            'limits':['Subset of mapped groups is not a full balanced 30-group score.','Legacy source answers are not semantically certified by source-span remapping.','Output status ANSWERED does not imply answer correctness.','This is a candidate development run, not frozen Config A/B/C final evaluation.'],
            'held_out_accessed':False,'archive_sha256':hashlib.sha256((source/'interactions.jsonl').read_bytes()).hexdigest()}
    (output/'summary.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input-name',required=True);main(p.parse_args().input_name)
