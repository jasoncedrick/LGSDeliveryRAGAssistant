"""Retry failed faithfulness only and audit paired development comparisons."""
from pathlib import Path
import json,sys,subprocess,os,hashlib,csv,math,copy,datetime
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'experiments'
METRICS=['faithfulness','context_precision','context_recall','answer_relevancy']
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def lines(p):return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def main():
 out=E/'t06-t07-development-closeout-v1';out.mkdir(exist_ok=True)
 paths=[E/f't07-development-abc-ragas-{c.lower()}-v1'/f for c in 'ABC' for f in ['scores.json','summary.json','judge_calls.jsonl']]+[E/f't07-development-abc-v1/{c}/interactions.jsonl' for c in 'ABC']
 hashes={str(p.relative_to(ROOT)):sha(p) for p in paths}
 if (out/'original_hashes.json').exists():assert read(out/'original_hashes.json')==hashes
 else:write(out/'original_hashes.json',hashes)
 scores={c:read(E/f't07-development-abc-ragas-{c.lower()}-v1/scores.json') for c in 'ABC'}
 originals=copy.deepcopy(scores);diagnoses=[]
 for c,rs in scores.items():
  for r in rs:
   failed=[m for m,v in r.get('scores',{}).items() if v is None]
   if not failed:continue
   assert failed==['faithfulness']
   name=f't07-faithfulness-retry-{c.lower()}-{r["record_id"].lower()}-v1'
   target=E/name
   diagnoses.append({'configuration':c,'record_id':r['record_id'],'original_scores':r['scores'].copy(),'retry_experiment':name,'cause':'Statement extraction continued unrelated examples' if c=='A' else 'NLI returned fractional 0.5 verdict and changed a statement'})
   if not (target/'summary.json').exists():
    if target.exists():raise RuntimeError('Partial retry exists; preserve for explicit inspection: '+name)
    print('Retrying',c,r['record_id'],flush=True)
    command=[sys.executable,'-B','scripts/score_development_ragas.py','--input-name','t07-development-abc-v1','--input-subdir',c,'--output-name',name,'--record-id',r['record_id'],'--metrics','faithfulness','--strict-faithfulness-json','--judge-output-tokens','4096','--judge-timeout','600']
    subprocess.run(command,cwd=ROOT,env=dict(os.environ,RAGAS_DO_NOT_TRACK='true'),check=True)
   retry=read(target/'scores.json')[0];diagnoses[-1]['retry_status']=retry['status'];diagnoses[-1]['retry_value']=retry['scores'].get('faithfulness')
   if retry['scores'].get('faithfulness') is not None:
    r['scores']['faithfulness']=retry['scores']['faithfulness'];r['status']='SCORED' if all(v is not None for v in r['scores'].values()) else 'PARTIAL_OR_FAILED_JUDGE'
 write(out/'judge_failure_review.json',diagnoses)
 archives={c:{r['record_id']:r for r in lines(E/f't07-development-abc-v1/{c}/interactions.jsonl')} for c in 'ABC'}
 ids=set(archives['A']);assert len(ids)==90 and all(set(a)==ids for a in archives.values())
 for rid in ids:
  assert len({archives[c][rid]['question'] for c in 'ABC'})==1
  assert len({archives[c][rid]['reference_answer'] for c in 'ABC'})==1
  assert all(archives[c][rid]['k']==3 for c in 'ABC')
 maps={c:{r['record_id']:r for r in rs} for c,rs in scores.items()}
 for c,rs in scores.items():write(out/f'scores_{c}.with_retries.json',rs)
 export=[];matched=[]
 for version,collection in [('original',originals),('supplemental_retries',scores)]:
  for c,rs in collection.items():
   for m in METRICS:
    values=[r['scores'][m] for r in rs if r['scores'].get(m) is not None]
    export.append({'version':version,'configuration':c,'metric':m,'mean':sum(values)/len(values),'valid_queries':len(values),'eligible_missing':sum(r['status']!='NOT_SCORED' and r['scores'].get(m) is None for r in rs),'not_scored':sum(r['status']=='NOT_SCORED' for r in rs)})
 for m in METRICS:
  common=sorted(rid for rid in ids if all(maps[c][rid]['scores'].get(m) is not None for c in 'ABC'))
  means={c:sum(maps[c][rid]['scores'][m] for rid in common)/len(common) for c in 'ABC'}
  pairs={}
  for left,right in [('B','A'),('B','C'),('C','A')]:
   diffs=[maps[left][rid]['scores'][m]-maps[right][rid]['scores'][m] for rid in common]
   pairs[left+'-'+right]={'mean_difference':sum(diffs)/len(diffs),'wins':sum(d>1e-9 for d in diffs),'ties':sum(abs(d)<=1e-9 for d in diffs),'losses':sum(d< -1e-9 for d in diffs)}
  matched.append({'metric':m,'n':len(common),'record_ids':common,'means':means,'paired_differences':pairs,'interpretation':'Descriptive, answer-eligible complete cases only. Not all-query effectiveness or significance evidence.'})
 write(out/'matched_query_comparison.json',matched)
 with (out/'comparison.with_retries.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=list(export[0]));w.writeheader();w.writerows(export)
 with (out/'matched_query_comparison.csv').open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=['metric','matched_queries','A','B','C','B_minus_A','B_minus_C']);w.writeheader()
  for x in matched:w.writerow({'metric':x['metric'],'matched_queries':x['n'],**x['means'],'B_minus_A':x['paired_differences']['B-A']['mean_difference'],'B_minus_C':x['paired_differences']['B-C']['mean_difference']})
 coverage={c:{s:sum(r['status']==s for r in a.values()) for s in sorted({r['status'] for r in a.values()})} for c,a in archives.items()}
 write(out/'coverage.json',coverage)
 bcf=[]
 for rid in sorted(ids):
  b,c=archives['B'][rid],archives['C'][rid]
  bcf.append({'record_id':rid,'same_normalized_query':b['normalization'].get('normalized_query')==c['normalization'].get('normalized_query'),'same_rankings':b['retrieved_rankings']==c['retrieved_rankings'],'same_answer':b['answer']==c['answer'],'B_status':b['status'],'C_status':c['status']})
 write(out/'bc_ablation_diagnostics.json',bcf)
 preserved=all(sha(ROOT/p)==h for p,h in hashes.items());assert preserved
 assessment={'T06':'COMPLETE_DEVELOPMENT_VALIDATED_HARNESS','T07_development':'COMPLETE_WITH_DOCUMENTED_LIMITATIONS' if all(r['scores'].get('faithfulness') is not None for rs in scores.values() for r in rs if r['status']!='NOT_SCORED') else 'DEVELOPMENT_RUN_COMPLETE_JUDGE_FAILURES_REMAIN','T07_full_manuscript':'NOT_COMPLETE_FREEZE_AND_HELD_OUT_COMPARISON_PENDING','held_out_accessed':False,'app_defaults_changed':False,'originals_preserved':preserved,'coverage':coverage,'near_tie_grid_warning':'Numerical winner differs from other candidates at floating-point epsilon; no meaningful superiority claim.','C_limitation':'Query-specific glossary injection removed; shared static lexical guidance retained.','source_limitations':'Source wording ambiguities and BFP detached context associations remain documented, not independently certified.','branch_checkpoint':'Development comparison and evaluator recovery; do not name branch as final held-out T07 completion.'}
 write(out/'completion_assessment.json',assessment)
 rows=['T06 and T07 development completion checkpoint','', 'T06: Evaluation harness implemented and development validated.','T07: Development grid, 270 A/B/C generation records and scoring completed.','Full T07 under manuscript: NOT COMPLETE. Registered freeze and single-pass held-out A/B/C comparison are pending.','', 'All 90 development queries retained per configuration. Original judge failures, answers and context archives preserved. Retry-only supplemental scoring is explicitly labeled.','Matched comparisons use the same answer-eligible query IDs for every system; they omit clarification and incomplete generation cases and are descriptive only. See coverage.json for all-query outcomes.','', 'Key evidence: matched_query_comparison.csv, comparison.with_retries.csv, judge_failure_review.json, completion_assessment.json.','', 'Before a final evaluation: review/document source ambiguities and BFP context association; confirm the exact freeze candidate including shared lexical guidance in C and the near-tied weight choice; register hashes for dictionary, corpus/indices, prompts, code, K and weights; then execute final held-out evaluation without tuning from test results.','', 'A new Git branch can preserve this checkpoint now. Suggested name: thesis/t06-t07-development-reviewed-20261019. Creating a branch does not itself commit or push any files.','', 'Grounding: 20260923.pdf Chapter 3.2.6 through 3.2.9; authoritative Thesis Tracker T06 harness and T07 three-architecture CSV tasks as archived in experiments/t06-formal-development-validation-v4/methodology_and_tracker.json. Tracker status itself is not rewritten.']
 (out/'READ_THIS_FIRST.txt').write_text('\n'.join(rows),encoding='utf-8')
 write(out/'hashes.json',{str(p.relative_to(out)):sha(p) for p in out.iterdir() if p.is_file() and p.name!='hashes.json'})
 print(json.dumps(assessment),flush=True)
if __name__=='__main__':main()
