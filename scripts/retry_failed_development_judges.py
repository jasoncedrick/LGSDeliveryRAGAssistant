"""Retry failed outputs only; immutable originals, explicit retry provenance."""
import json, hashlib, pathlib, shutil, requests, subprocess, sys, os, copy
ROOT=pathlib.Path(__file__).resolve().parents[1]
E=ROOT/'experiments'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def lines(p): return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines()]
def write(p,d): p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=E/'failed-judge-retry-v2'; out.mkdir(exist_ok=True)
 original=E/'t06-ragas-reviewed-development-v2';grid=E/'t07-development-grid-v1'
 files=[original/'scores.json',original/'judge_calls.jsonl',grid/'judge_verdicts.jsonl',grid/'context_precision_grid.json']
 hashes={str(p.relative_to(ROOT)):sha(p) for p in files}
 write(out/'original_hashes.json',hashes)
 tasks=[];pending={}
 for x in lines(original/'judge_calls.jsonl'):
  if x['event']=='judge_prompt':
   for prompt in x['prompts']:
    if 'top-level JSON array' in prompt and x['record_id'].startswith('SCENARIO-BB-001-'): pending[x['record_id']]=prompt
 for r in read(original/'scores.json'):
  if r['scores'].get('context_recall','absent') is None:
   tasks.append({'record_id':r['record_id'],'metric':'context_recall','prompt':pending[r['record_id']]})
 failed=[x for x in lines(grid/'judge_verdicts.jsonl') if x['status']!='SCORED']
 assert len(failed)==1
 tasks.append({**failed[0],'metric':'context_precision'})
 results=[]
 for i,t in enumerate(tasks):
  target=out/f'retry_{i}.json'
  if target.exists():results.append(read(target));continue
  recall=t['metric']=='context_recall'
  suffix='' if recall else '\nReturn exactly ONE JSON object with reason and verdict for the WHOLE supplied context. Do not emit multiple objects or per-statement verdicts.'
  payload={'model':'eboss-mistral','prompt':t['prompt']+suffix,'stream':False,'options':{'temperature':0,'top_p':0,'num_ctx':8192,'num_predict':4096 if recall else 1024,'num_thread':4}}
  item={'record_id':t['record_id'],'metric':t['metric'],'original_prompt_sha256':hashlib.sha256(t['prompt'].encode()).hexdigest(),'request':payload,'status':'FAILED','parsed':None}
  print(f'Retrying {i+1}/4 {t["record_id"]} {t["metric"]}',flush=True)
  try:
   response=requests.post('http://localhost:11434/api/generate',json=payload,timeout=600);response.raise_for_status(); data=response.json();item['response']=data
   parsed=json.loads(data['response'])
   valid=(isinstance(parsed,list) and bool(parsed) and all(isinstance(v,dict) and v.get('Attributed') in ('0','1') for v in parsed)) if recall else (isinstance(parsed,dict) and isinstance(parsed.get('reason'),str) and parsed.get('verdict') in ('0','1'))
   if valid and data.get('done') and data.get('done_reason')!='length': item.update(status='SCORED',parsed=parsed)
  except Exception as exc:item['error']=str(exc)
  write(target,item);results.append(item);print(item['status'],flush=True)
 revised=E/'t07-development-grid-format-retry-v2';revised.mkdir(exist_ok=True)
 for name in ['rankings.jsonl','protocol.json','validation.json']:shutil.copy2(grid/name,revised/name)
 verdicts=lines(grid/'judge_verdicts.jsonl');retry=results[-1]
 if retry['status']=='SCORED':
  for item in verdicts:
   if item['prompt_sha256']==failed[0]['prompt_sha256']:
    item.update(parsed=retry['parsed'],status='SCORED',raw_output=retry['response']['response'],origin='format_retry',retry_artifact=str(out/'retry_3.json'),original_cache_sha256=sha(grid/'judge_verdicts.jsonl'))
 (revised/'judge_verdicts.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in verdicts),encoding='utf-8')
 env=dict(os.environ,T07_GRID_DIRECTORY=revised.name,RAGAS_DO_NOT_TRACK='true')
 subprocess.run([sys.executable,'-B',str(ROOT/'scripts/judge_t07_development_grid.py')],env=env,cwd=ROOT,check=True,stdout=(out/'grid_recompute.log').open('w'))
 scores=copy.deepcopy(read(original/'scores.json'))
 for r in scores:
  for retry in results[:3]:
   if retry['record_id']==r['record_id'] and retry['status']=='SCORED':r['scores']['context_recall']=sum(int(v['Attributed']) for v in retry['parsed'])/len(retry['parsed'])
  if r['record_id']==failed[0]['record_id'] and results[-1]['status']=='SCORED':
   dataset=read(original/('dataset_'+r['record_id']+'.json')); contexts=dataset['contexts'][0];vs=[]
   for context in contexts:
    matches=[v for v in verdicts if v['record_id']==r['record_id'] and context in v['prompt']]
    assert len(matches)==1
    vs.append(int(matches[0]['parsed']['verdict']))
   r['scores']['context_precision']=sum((sum(vs[:i+1])/(i+1))*v for i,v in enumerate(vs))/(sum(vs)+1e-10)
  if r['scores']:r['status']='SCORED' if all(v is not None for v in r['scores'].values()) else 'PARTIAL_OR_FAILED_JUDGE'
 write(out/'scores.with_retries.json',scores)
 aggregates={}
 for metric in ['faithfulness','context_precision','context_recall','answer_relevancy']:
  values=[r['scores'][metric] for r in scores if r['scores'].get(metric) is not None]
  aggregates[metric]={'valid':len(values),'mean':sum(values)/len(values)}
 write(out/'summary.json',{'retry_results':[{k:r[k] for k in ['record_id','metric','status']} for r in results],'metric_aggregates':aggregates,'originals_preserved':all(sha(ROOT/p)==v for p,v in hashes.items()),'held_out_accessed':False,'note':'Supplemental retry-adjusted scores; original run retained. Recall output ceiling 4096; precision one-object format suffix. No answer/reference/context edits.'})
 assert all(sha(ROOT/p)==v for p,v in hashes.items())
 print('Retries and grid recomputation finished',flush=True)
if __name__=='__main__':main()
