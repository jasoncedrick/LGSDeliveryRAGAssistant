"""Preserve base grid, recover format failures separately, recompute the same objective."""
from pathlib import Path
import json,hashlib,time,subprocess,sys,os,requests,shutil
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'experiments'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 source=E/'punctuation-context-precision-v1'
 while not (source/'baseline_comparison.json').exists():time.sleep(10)
 items=[json.loads(l) for l in (source/'judge_verdicts.jsonl').read_text(encoding='utf-8').splitlines()]
 failed=[x for x in items if x['status']!='SCORED']
 if not failed:print('No format recovery required');return
 out=E/'punctuation-context-precision-format-retry-v2';out.mkdir(exist_ok=True)
 original_hash=sha(source/'judge_verdicts.jsonl');recovered={};audits=[]
 prior=read(E/'failed-judge-retry-v2/retry_3.json')
 for number,item in enumerate(failed):
  key=item['prompt_sha256'];path=out/f'retry_{number}.json'
  if path.exists():retry=read(path)
  elif key==prior['original_prompt_sha256'] and prior['status']=='SCORED':
   assert prior['request']['prompt'].startswith(item['prompt'])
   retry={**prior,'origin':'reused_identical_prior_format_retry_request','original_retry_file':str(E/'failed-judge-retry-v2/retry_3.json')}
  else:
   prompt=item['prompt']+'\nReturn exactly ONE JSON object with reason and verdict for the WHOLE supplied context. Do not emit multiple objects or per-statement verdicts.'
   payload={'model':'eboss-mistral','prompt':prompt,'stream':False,'options':{'temperature':0,'top_p':0,'num_ctx':8192,'num_predict':1024,'num_thread':4}}
   retry={'original_prompt_sha256':key,'request':payload,'status':'FAILED','parsed':None,'origin':'new_failed_output_only_retry'}
   try:
    response=requests.post('http://localhost:11434/api/generate',json=payload,timeout=120);response.raise_for_status();retry['response']=response.json();parsed=json.loads(retry['response']['response'])
    if isinstance(parsed,dict) and isinstance(parsed.get('reason'),str) and parsed.get('verdict') in ('0','1') and retry['response'].get('done_reason')!='length':retry.update(status='SCORED',parsed=parsed)
   except Exception as exc:retry['error']=str(exc)
  assert retry['original_prompt_sha256']==key
  path.write_text(json.dumps(retry,ensure_ascii=False,indent=2),encoding='utf-8');audits.append({'record_id':item['record_id'],'chunk_id':item['chunk_id'],'status':retry['status'],'origin':retry['origin']})
  if retry['status']=='SCORED':recovered[key]={**item,'parsed':retry['parsed'],'raw_output':retry['response']['response'],'status':'SCORED','origin':'format_retry','retry_artifact':str(path),'original_cache_sha256':original_hash}
 for filename in ['rankings.jsonl','protocol.json','validation.json','METHOD_ALIGNMENT.txt']:shutil.copy2(source/filename,out/filename)
 (out/'judge_verdicts.jsonl').write_text(''.join(json.dumps(recovered.get(x['prompt_sha256'],x),ensure_ascii=False)+'\n' for x in items),encoding='utf-8')
 env=dict(os.environ,T07_GRID_DIRECTORY=out.name,RAGAS_DO_NOT_TRACK='true')
 with (out/'console.log').open('w',encoding='utf-8') as log:subprocess.run([sys.executable,'-B','scripts/judge_t07_development_grid.py'],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
 assert sha(source/'judge_verdicts.jsonl')==original_hash
 d=read(out/'context_precision_grid.json');b=read(E/'t07-development-grid-format-retry-v2/context_precision_grid.json')
 comparison={'selection_status':d['selection_status'],'candidate_best':d['best_complete_candidate'],'baseline_best':b['best_complete_candidate'],'judge_recovery':audits,'originals_preserved':True,'held_out_accessed':False,'freeze':False}
 if d['best_complete_candidate']:comparison['J_difference']=d['best_complete_candidate']['J']-b['best_complete_candidate']['J']
 (out/'baseline_comparison.json').write_text(json.dumps(comparison,indent=2),encoding='utf-8')
 best=d['best_complete_candidate'];weights=read(out/'protocol.json')['weight_grid'][best['grid_id']] if best else None
 text=['SUPPLEMENTAL PUNCTUATION GRID REVIEW','',json.dumps(comparison,indent=2),'',f'Candidate weights: {weights}','Original invalid outputs remain in punctuation-context-precision-v1. Supplemental verdicts are format retries with original prompt hashes and exact request provenance. No score-level imputation.','Same 90 development queries, 17 weight combinations and K3/K5. No held-out access, answer regeneration, deployment or freeze.','A complete objective grid is development evidence, not official expert certification or final T07 completion. Review source coverage and normalization limitations before deciding to regenerate paired answers.']
 (out/'REVIEW_RESULTS.txt').write_text('\n'.join(text),encoding='utf-8')
 (out/'hashes.json').write_text(json.dumps({p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='hashes.json'},indent=2),encoding='utf-8')
 state=E/'t06-t07-current-status';status=read(state/'status.json');status.update(t07='Punctuation Context Precision supplemental grid finished; '+d['selection_status'],objective_review=str(out/'REVIEW_RESULTS.txt'));(state/'status.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
 with (state/'READ_THIS_FIRST.txt').open('a',encoding='utf-8') as f:f.write('\nSUPPLEMENTAL FORMAT RECOVERY REVIEW: experiments/punctuation-context-precision-format-retry-v2/REVIEW_RESULTS.txt\nNo deployment or freeze.\n')
 print(json.dumps(comparison),flush=True)
if __name__=='__main__':main()
