"""One format-only retry for invalid calibration outputs; never retry wrong valid labels."""
from pathlib import Path
import sys,json,hashlib,time,copy,requests,collections
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.context_precision_judge_v2 import FORMAT_RETRY_SUFFIX
from src.offline_judge_grounding import parse_grounded_verdict
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
 source=ROOT/'experiments/context-precision-calibration-v2'
 while not (source/'summary.json').exists():time.sleep(10)
 out=ROOT/'experiments/context-precision-calibration-v2-format-retry';out.mkdir(exist_ok=True)
 source_hash=sha(source/'results.jsonl');results=[json.loads(l) for l in (source/'results.jsonl').read_text(encoding='utf-8').splitlines()];original=copy.deepcopy(results);cases={r['case_id']:r for r in read(source/'controls.snapshot.json')}
 write(out/'protocol.json',{'source_results_sha256':source_hash,'retry_suffix':FORMAT_RETRY_SUFFIX,'retry_policy':'Exactly one retry per invalid output; no valid disagreement is retried. All 60 original cases retained. Invalid remains missing.','held_out_accessed':False,'original_scores_changed':False,'scope':'Supplemental evaluator format recovery, not independent validation'})
 for i,r in enumerate(results):
  if r['status']=='VALID':continue
  file=out/(r['case_id']+'.json')
  if file.exists():retry=read(file)
  else:
   payload=copy.deepcopy(r['request']);payload['prompt']+=FORMAT_RETRY_SUFFIX;retry={'case_id':r['case_id'],'request':payload,'original_prompt_sha256':r['prompt_sha256'],'parsed':None,'status':'ERROR'}
   try:
    response=requests.post('http://localhost:11434/api/generate',json=payload,timeout=120);response.raise_for_status();data=response.json();retry['response']=data
    value,error=parse_grounded_verdict(data['response'],cases[r['case_id']]['context'])
    if data.get('done_reason')=='length':value=None;error='TRUNCATED'
    retry.update(parsed=value,error=error,status='VALID' if value else 'INVALID')
   except Exception as exc:retry['error']=str(exc)
   write(file,retry)
  if retry['status']=='VALID':results[i]={**r,'parsed':retry['parsed'],'status':'VALID','label_correct':retry['parsed']['verdict']==r['expected_verdict'],'retry_artifact':str(file),'original_status':r['status']}
  print('Format retry',r['case_id'],retry['status'],flush=True)
 valid=[r for r in results if r['status']=='VALID'];fp=[r['case_id'] for r in valid if r['expected_verdict']=='0' and r['parsed']['verdict']=='1'];fn=[r['case_id'] for r in valid if r['expected_verdict']=='1' and r['parsed']['verdict']=='0']
 summary={'cases':60,'valid_after_retries':len(valid),'invalid_remaining':60-len(valid),'correct_over_all_controls':sum(r.get('label_correct',False) for r in results)/60,'FP':len(fp),'FN':len(fn),'false_positive_cases':fp,'false_negative_cases':fn,'valid_disagreements_not_retried':True,'original_results_preserved':sha(source/'results.jsonl')==source_hash,'held_out_accessed':False,'interpretation':'Development sanity-check evidence only; report residual judge errors and repeated-control limitation. Not expert certification.'}
 write(out/'results.with_retries.json',results);write(out/'summary.json',summary);write(out/'hashes.json',{p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='hashes.json'});print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
