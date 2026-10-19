"""Consolidate reviewed development candidates and rescore unchanged archived rankings."""
import json,hashlib,csv,sys,copy
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.development_retrieval_metrics import ranking_metrics
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 src=ROOT/'experiments/t06-formal-development-validation-v3';out=ROOT/'experiments/t06-formal-development-validation-v4'
 if out.exists():raise ValueError('Output must be fresh')
 old=read(src/'development_groups.derived.json');updated=copy.deepcopy(old);changes=[];inputs=[src/'development_groups.derived.json',src/'interactions.corrected_references.jsonl']
 for idx,g in enumerate(old):
  gid=g['group_id'];office=gid.split('-')[1];num=int(gid.split('-')[2]);folder=ROOT/'experiments'/f'source-reference-review-bb{num:03d}-v1' if office=='BB' and num<=5 else ROOT/'experiments/source-reference-review-remaining-batch-v1'/gid
  if (folder/'group.candidate.json').exists():
   candidate=read(folder/'group.candidate.json');review=read(folder/'review.json');assert candidate['queries']==g['queries'] and candidate['split']=='development'
   candidate['source_review_status']=review['review_status'];candidate['source_limitations']=review.get('limitations',[]);candidate['source_review_path']=str(folder.relative_to(ROOT)/'review.json');candidate['independent_expert_certified']=False
   updated[idx]=candidate;inputs += [folder/'group.candidate.json',folder/'review.json'];changes.append({'group_id':gid,'old_reference':g['ground_truth_reference_answer'],'new_reference':candidate['ground_truth_reference_answer'],'old_ids':g['ground_truth_chunk_ids'],'new_ids':candidate['ground_truth_chunk_ids'],'review_status':review['review_status']})
 assert len(changes)==25 and len(updated)==30
 corpus=read(ROOT/'experiments/chapter3-table-repaired-development-v1/corpus.json');valid={c['chunk_id'] for c in corpus}
 assert all(g['ground_truth_chunk_ids'] and set(g['ground_truth_chunk_ids'])<=valid for g in updated)
 records=[json.loads(l) for l in inputs[1].read_text(encoding='utf-8').splitlines()];assert len(records)==90
 byid={g['group_id']:g for g in updated};newrecords=[];metrics=[]
 for record in records:
  r=copy.deepcopy(record);g=byid[r['question_group_id']];assert r['question']==g['queries'][r['language']]
  r['previous_reference_answer']=r['reference_answer'];r['previous_ground_truth_chunk_ids']=r['ground_truth_chunk_ids'];r['previous_ranking_metrics']=r['ranking_metrics']
  r.update(reference_answer=g['ground_truth_reference_answer'],ground_truth_chunk_ids=g['ground_truth_chunk_ids'],reference_status=g['mapping_status'],relevance_mapping_status=g['mapping_status'],source_review_status=g.get('source_review_status',g['mapping_status']))
  r['ranking_metrics']={str(k):ranking_metrics(r['retrieved_rankings'].get(str(k),[]),g['ground_truth_chunk_ids'],k) for k in (3,5)}
  for key in ['answer','context','citations','retrieved_rankings','normalization','status']:
   assert r.get(key)==record.get(key)
  newrecords.append(r)
  for k in (3,5):metrics.append({'record_id':r['record_id'],'group_id':r['question_group_id'],'pillar':r['pillar'],'language':r['language'],'status':r['status'],'k':k,**r['ranking_metrics'][str(k)]})
 out.mkdir();write=lambda n,d:(out/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 write('development_groups.derived.json',updated);write('reference_changes.json',changes);write('development_groups.before.json',old)
 (out/'interactions.corrected_references.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in newrecords),encoding='utf-8')
 with (out/'per_query_metrics.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(metrics[0]));w.writeheader();w.writerows(metrics)
 sums=[]
 for k in (3,5):
  rows=[r for r in metrics if r['k']==k];sums.append({'k':k,'queries':len(rows),'hits':sum(r['hit_at_k'] for r in rows),'hit_at_k':sum(r['hit_at_k'] for r in rows)/len(rows),'mrr_at_k':sum(r['mrr_at_k'] for r in rows)/len(rows)})
 protocol={'held_out_accessed':False,'app_defaults_changed':False,'scope':'All 90 archived development outcomes retained; reference-only correction, not a new retrieval run.','groups':30,'queries':90,'generation_k':5,'ranking_k':[3,5],'source_limits':'User interpretations and source conflicts remain explicit; these are reviewed development references, not independently certified gold. No exclusions to improve reported results.','freeze':False}
 write('protocol.json',protocol);write('summary.json',{**protocol,'status':'REVIEWED_REFERENCES_CONSOLIDATED_ARCHIVED_RANKINGS_RESCORED','changed_groups':25,'statuses':dict(Counter(r['status'] for r in newrecords)),'ranking_metrics':sums,'offline_ragas':'pending new reference-dependent scores; earlier scores retained separately'})
 write('input_hashes.json',{str(p.relative_to(ROOT)):sha(p) for p in inputs});write('methodology_and_tracker.json',read(src/'methodology_and_tracker.json'))
 write('validation.json',{'unique_records':len({r['record_id'] for r in newrecords}),'all_relevance_ids_exist':True,'archived_outputs_rankings_and_contexts_unchanged':True,'source_answers_preserved':True,'no_held_out_access':True})
 (out/'READ_THIS_FIRST.txt').write_text('V4 REVIEWED DEVELOPMENT REFERENCES\nAll 30 groups / 90 queries retained. 25 reviewed candidates consolidated; 5 previously corrected references retained. User interpretations and source limitations remain explicit. Original v3, generated answers, contexts and rankings unchanged. per_query_metrics.csv rescored at K3/K5. This is a label correction, not improved/reduced retrieval performance. Independent expert certification and final freeze remain separate.\n',encoding='utf-8')
 write('hashes.json',{p.name:sha(p) for p in out.iterdir() if p.is_file()});print(json.dumps(sums))
if __name__=='__main__':main()
