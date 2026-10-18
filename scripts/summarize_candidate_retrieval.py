"""Pair fixed-label development retrieval runs and export auditable ranking metrics."""
import csv
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.evaluate_source_evidence_dev import covers
from src.development_retrieval_metrics import ranking_metrics


def main():
    baseline=ROOT/'experiments/source-evidence-development-v2'
    candidate=ROOT/'experiments/source-evidence-development-v4-intent-candidate'
    output=ROOT/'experiments/candidate-retrieval-comparison-v1'
    if output.exists():raise ValueError('Preserve prior comparison')
    read=lambda path:json.loads(path.read_text(encoding='utf-8'))
    questions=read(baseline/'questions.json')
    assert questions==read(candidate/'questions.json'),'Labels differ; not a paired comparison'
    assert read(baseline/'summary.json')['artifact_hashes']==read(candidate/'summary.json')['artifact_hashes'],'Corpus/index/dictionary hashes differ'
    chunks=read(ROOT/'experiments/chapter3-table-repaired-development-v1/corpus.json')
    gold={}
    for q in questions:
        if q['kind']=='answerable':
            gold[q['id']]=[c['chunk_id'] for c in chunks if c['source_page_id']==q['source_page_id'] and any(covers(c['text_content'],g) for g in q['evidence_groups'])]
            assert gold[q['id']],q['id']
    variants=[('raw',read(candidate/'results.json'),'raw'),('previous_normalization',read(baseline/'results.json'),'normalized'),('candidate_normalization',read(candidate/'results.json'),'normalized')]
    rows=[]
    for variant,results,mode in variants:
        for result in results:
            if result['kind']!='answerable' or result['mode']!=mode:continue
            ids=[c['chunk_id'] for c in result.get('returned',[])]
            metrics=ranking_metrics(ids,gold[result['id']],result['k'])
            rows.append({'variant':variant,'id':result['id'],'k':result['k'],'retrieval_status':result['status'],**metrics,
                         'page_hit':int(result.get('page_hit',False)),'complete_evidence':int(result.get('all_evidence_groups_covered',False))})
    summary=[]
    for variant,_,_ in variants:
        for k in (3,5):
            subset=[r for r in rows if r['variant']==variant and r['k']==k]
            assert len(subset)==12
            summary.append({'variant':variant,'k':k,'queries':12,'hit_at_k':sum(r['hit_at_k'] for r in subset)/12,
                            'mrr_at_k':sum(r['mrr_at_k'] for r in subset)/12,
                            'complete_evidence_hits':sum(r['complete_evidence'] for r in subset),
                            'failed_complete_evidence_ids':[r['id'] for r in subset if not r['complete_evidence']]})
    output.mkdir()
    with (output/'per_query_metrics.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    report={'status':'PAIRED_DEVELOPMENT_DIAGNOSTIC','summary':summary,'paired_inputs_verified':True,
            'relevance_definition':'A relevant chunk co-locates all fragments of at least one labelled evidence group on the expected page. Complete evidence is separately measured across all groups.',
            'limitations':['Labels remain provisional except reviewed cases; lexical matches are not semantic proof.','These 12 English questions are not the formal 30-group multilingual development evaluation.','Hit@K and MRR@K are retrieval metrics; no RAGAS or generated-answer quality is claimed.'],
            'app_changed':False,'held_out_accessed':False,'weights_changed':False,'ragas_run':False}
    (output/'summary.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    (output/'relevance_labels.json').write_text(json.dumps(gold,indent=2),encoding='utf-8')
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for directory in (baseline,candidate) for p in [directory/'questions.json',directory/'results.json',directory/'normalizations.json',directory/'summary.json']}
    hashes.update({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.is_file()})
    (output/'hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
