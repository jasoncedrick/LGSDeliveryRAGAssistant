"""Test one fixed template revision on all previously declared source controls."""
from pathlib import Path
import sys,json,hashlib,datetime,collections,os
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.context_precision_judge_v2 import VERSION,PROMPT_TEMPLATE,build_prompt
from src.offline_judge_grounding import parse_grounded_verdict
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 import requests
 old=ROOT/'experiments/context-precision-calibration-v1';out=ROOT/'experiments/context-precision-calibration-v2';out.mkdir(exist_ok=True)
 cases=read(old/'controls.json');assert len(cases)==60;assert sha(old/'controls.json')==read(old/'protocol.json')['controls_sha256']
 models=requests.get('http://localhost:11434/api/tags',timeout=10).json()['models'];model=next(m for m in models if m['name']=='eboss-mistral:latest');assert model['digest']==read(old/'runtime_provenance.json')['model_digest']
 protocol={'version':VERSION,'controls_sha256':sha(old/'controls.json'),'template_sha256':hashlib.sha256(PROMPT_TEMPLATE.encode()).hexdigest(),'model_digest':model['digest'],'settings':{'temperature':0,'top_p':0,'num_ctx':8192,'num_predict':1024,'num_thread':4},'scope':'Adaptive development evaluator calibration; not final or independent validation','examples':'Three fictional library-format examples, not official-source reconstructions or benchmark scenarios','reference_grounding':'20260923.pdf PDF25 and31-34, offline RAGAS and development-only tuning; main Thesis Tracker archived T06 harness requirement','mathematics':'RAGAS 0.1.5 ranked average precision unchanged; evidence/format errors remain missing','held_out_accessed':False,'app_defaults_changed':False,'original_scores_changed':False,'promotion_policy':'No automatic acceptance from JSON validity. Report confusion matrix and failures across every office/language; preserve original evaluator alongside revision.'}
 if (out/'protocol.json').exists():assert read(out/'protocol.json')==protocol
 else:
  write(out/'protocol.json',protocol);write(out/'controls.snapshot.json',cases);(out/'prompt_template.txt').write_text(PROMPT_TEMPLATE,encoding='utf-8')
 lock=out/'judge.lock'
 try:fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
 except FileExistsError:raise SystemExit('Calibration already running.')
 os.write(fd,str(os.getpid()).encode());os.close(fd)
 try:
  resultsfile=out/'results.jsonl';results=[json.loads(l) for l in resultsfile.read_text(encoding='utf-8').splitlines()] if resultsfile.exists() else [];done={r['case_id'] for r in results}
  def log(t):
   print(t,flush=True)
   with (out/'console.log').open('a',encoding='utf-8') as f:f.write(t+'\n')
  for c in cases:
   if c['case_id'] in done:continue
   prompt=build_prompt(c['question'],c['reference_answer'],c['context']);payload={'model':'eboss-mistral','prompt':prompt,'stream':False,'options':protocol['settings']}
   r={'case_id':c['case_id'],'pillar':c['pillar'],'language':c['language'],'expected_verdict':c['expected_verdict'],'request':payload,'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'status':'ERROR','parsed':None,'raw_verdict':None}
   try:
    response=requests.post('http://localhost:11434/api/generate',json=payload,timeout=120);response.raise_for_status();data=response.json();r['raw_output']=data['response'];r['response_metadata']={k:v for k,v in data.items() if k not in ('context','response')}
    try:r['raw_verdict']=json.loads(data['response']).get('verdict')
    except (ValueError,AttributeError):pass
    parsed,error=parse_grounded_verdict(data['response'],c['context'])
    if data.get('done_reason')=='length':parsed=None;error='TRUNCATED'
    r.update(parsed=parsed,error=error,status='VALID' if parsed else 'INVALID')
    if parsed:r['label_correct']=parsed['verdict']==c['expected_verdict']
   except Exception as exc:r['error']=str(exc)
   with resultsfile.open('a',encoding='utf-8') as f:f.write(json.dumps(r,ensure_ascii=False)+'\n')
   results.append(r);write(out/'progress.json',{'completed':len(results),'total':60,'latest':{'case_id':c['case_id'],'status':r['status']}});log(f'{len(results)}/60 {c["case_id"]} {r["status"]} expected={c["expected_verdict"]} observed={r["raw_verdict"]}')
  assert len(results)==60 and len({r['case_id'] for r in results})==60
  def stats(rs):
   valid=[r for r in rs if r['status']=='VALID'];tp=sum(r['expected_verdict']=='1' and r['parsed']['verdict']=='1' for r in valid);tn=sum(r['expected_verdict']=='0' and r['parsed']['verdict']=='0' for r in valid)
   return {'n':len(rs),'valid':len(valid),'invalid':len(rs)-len(valid),'TP':tp,'TN':tn,'FP':sum(r['expected_verdict']=='0' and r['parsed']['verdict']=='1' for r in valid),'FN':sum(r['expected_verdict']=='1' and r['parsed']['verdict']=='0' for r in valid),'correct_over_all_controls':(tp+tn)/len(rs),'raw_FP_including_invalid':sum(r['expected_verdict']=='0' and r.get('raw_verdict')=='1' for r in rs),'raw_FN_including_invalid':sum(r['expected_verdict']=='1' and r.get('raw_verdict')=='0' for r in rs),'failure_types':dict(collections.Counter(r.get('error') for r in rs if r['status']!='VALID'))}
  summary={'overall':stats(results),'by_office_language':{p+'|'+l:stats([r for r in results if r['pillar']==p and r['language']==l]) for p in sorted({r['pillar'] for r in results}) for l in ['english','taglish','bislish']},'original_baseline':read(old/'summary.json')['results']['baseline'],'held_out_accessed':False,'freeze':False,'limits':'Same assistant-labeled development controls reused; adaptive diagnostics, not independent expert or held-out certification.'}
  write(out/'summary.json',summary);assert sha(old/'controls.json')==protocol['controls_sha256'];write(out/'hashes.json',{p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name not in ('hashes.json','judge.lock')});log('Fixed-template calibration complete; review summary before any promotion.')
 finally:lock.unlink()
if __name__=='__main__':main()
