"""Resumable offline original/candidate judge calibration; no score replacement."""
from pathlib import Path
import sys,json,hashlib,copy,os,datetime,collections
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.offline_judge_grounding import INSTRUCTION,parse_grounded_verdict
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def lines(p):return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def main():
 import requests
 from ragas.metrics import context_precision
 from src.ragas_output_contracts import apply_contracts
 out=ROOT/'experiments/context-precision-calibration-v1';protocol=read(out/'protocol.json');assert sha(out/'controls.json')==protocol['controls_sha256'];assert sha(out/'candidate_instruction.txt')==protocol['candidate_instruction_sha256']
 cases=read(out/'controls.json');assert len(cases)==60
 models=requests.get('http://localhost:11434/api/tags',timeout=10).json()['models'];model=next(m for m in models if m['name']=='eboss-mistral:latest');assert model['digest']==read(ROOT/'experiments/t07-development-abc-v1/protocol.json')['model_digest']
 lock=out/'judge.lock'
 try:fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
 except FileExistsError:raise SystemExit('Calibration already running; inspect progress.')
 os.write(fd,str(os.getpid()).encode());os.close(fd)
 try:
  ms={v:copy.deepcopy(context_precision) for v in ['baseline','evidence_candidate']};apply_contracts({'context_precision':ms['baseline']});ms['evidence_candidate'].context_precision_prompt.instruction+='\n'+INSTRUCTION
  prompts={v:m.context_precision_prompt.instruction for v,m in ms.items()};write(out/'judge_instructions.json',prompts)
  write(out/'runtime_provenance.json',{'model_digest':model['digest'],'settings':{'temperature':0,'top_p':0,'num_ctx':8192,'num_predict':1024,'num_thread':4},'app_defaults_changed':False,'held_out_accessed':False})
  cache={}
  for folder in ['t07-development-grid-v1','punctuation-context-precision-v1']:
   for x in lines(ROOT/'experiments'/folder/'judge_verdicts.jsonl'):
    if x['status']=='SCORED' and x.get('origin')!='format_retry' and hashlib.sha256(x['prompt'].encode()).hexdigest()==x['prompt_sha256']:cache[x['prompt_sha256']]=x
  path=out/'results.jsonl';results=lines(path) if path.exists() else [];done={(r['case_id'],r['judge_version']) for r in results}
  def log(t):
   print(t,flush=True)
   with (out/'console.log').open('a',encoding='utf-8') as f:f.write(t+'\n')
  for case in cases:
   for version,m in ms.items():
    if (case['case_id'],version) in done:continue
    prompt=m._context_precision_prompt({'question':case['question'],'contexts':[case['context']],'ground_truth':case['reference_answer']})[0].to_string();key=hashlib.sha256(prompt.encode()).hexdigest();payload={'model':'eboss-mistral','prompt':prompt,'stream':False,'options':{'temperature':0,'top_p':0,'num_ctx':8192,'num_predict':1024,'num_thread':4}}
    item={'case_id':case['case_id'],'group_id':case['group_id'],'pillar':case['pillar'],'language':case['language'],'chunk_id':case['chunk_id'],'judge_version':version,'expected_verdict':case['expected_verdict'],'request':payload,'prompt_sha256':key,'parsed':None,'status':'ERROR'}
    try:
     if version=='baseline' and key in cache:raw=cache[key]['raw_output'];item['origin']='exact_original_prompt_cache'
     else:
      response=requests.post('http://localhost:11434/api/generate',json=payload,timeout=120);response.raise_for_status();data=response.json();raw=data['response'];item['response_metadata']={k:v for k,v in data.items() if k!='context'};item['origin']='new_judge_call'
     item['raw_output']=raw
     try:rawverdict=json.loads(raw).get('verdict');item['raw_verdict']=rawverdict if rawverdict in ('0','1') else None
     except (ValueError,TypeError,AttributeError):item['raw_verdict']=None
     if version=='evidence_candidate':parsed,error=parse_grounded_verdict(raw,case['context'])
     else:
      try:
       parsed=json.loads(raw);error=None
       if not isinstance(parsed,dict) or not isinstance(parsed.get('reason'),str) or parsed.get('verdict') not in ('0','1'):parsed=None;error='INVALID_SCHEMA'
      except (ValueError,TypeError):parsed=None;error='INVALID_JSON'
     if item.get('response_metadata',{}).get('done_reason')=='length':parsed=None;error='TRUNCATED'
     item.update(parsed=parsed,status='VALID' if parsed else 'INVALID',error=error)
     if parsed:item['label_correct']=parsed['verdict']==case['expected_verdict']
    except Exception as exc:item.update(error=str(exc),status='REQUEST_ERROR')
    with path.open('a',encoding='utf-8') as f:f.write(json.dumps(item,ensure_ascii=False)+'\n')
    results.append(item);write(out/'progress.json',{'completed':len(results),'total':120,'latest':{'case_id':case['case_id'],'judge_version':version,'status':item['status']}});log(f"{len(results)}/120 {version} {case['case_id']} {item['status']} expected={case['expected_verdict']} observed={item.get('raw_verdict')}")
  assert len(results)==120 and len({(r['case_id'],r['judge_version']) for r in results})==120
  def stats(rs):
   valid=[r for r in rs if r['status']=='VALID'];positive=[r for r in valid if r['expected_verdict']=='1'];negative=[r for r in valid if r['expected_verdict']=='0'];tp=sum(r['parsed']['verdict']=='1' for r in positive);tn=sum(r['parsed']['verdict']=='0' for r in negative)
   return {'n':len(rs),'valid':len(valid),'invalid_or_error':len(rs)-len(valid),'correct_valid':tp+tn,'accuracy_on_valid':(tp+tn)/len(valid) if valid else None,'correct_over_all_controls':(tp+tn)/len(rs) if rs else None,'TP':tp,'FN':len(positive)-tp,'TN':tn,'FP':len(negative)-tn,'raw_false_positives_including_invalid_quotes':sum(r['expected_verdict']=='0' and r.get('raw_verdict')=='1' for r in rs),'raw_false_negatives_including_invalid_quotes':sum(r['expected_verdict']=='1' and r.get('raw_verdict')=='0' for r in rs),'failure_types':dict(collections.Counter(r.get('error') for r in rs if r['status']!='VALID'))}
  summary={v:stats([r for r in results if r['judge_version']==v]) for v in ms}
  bycell={v:{p+'|'+l:stats([r for r in results if r['judge_version']==v and r['pillar']==p and r['language']==l]) for p in sorted({c['pillar'] for c in cases}) for l in ['english','taglish','bislish']} for v in ms}
  write(out/'summary.json',{'results':summary,'by_office_language':bycell,'labels_sha256':sha(out/'controls.json'),'held_out_accessed':False,'original_scores_changed':False,'decision':'REVIEW_CALIBRATION_BEFORE_ANY_EVALUATOR_PROMOTION','limits':['Small assistant-labeled development calibration set; not independent expert gold or a new final benchmark.','Verbatim quotation validates provenance, not semantic usefulness.','Invalid outputs remain missing and count against all-control correct coverage.','Known development examples do not establish held-out evaluator generalization.']})
  text=['OFFLINE CONTEXT PRECISION CALIBRATION','', '60 source-grounded controls; two positive and two negative contexts in each of 15 office-language cells. All labels declared and hashed before new calls.','',json.dumps(summary,indent=2),'','Review raw_false_positives_including_invalid_quotes as well as FP. A judge can quote real but irrelevant text; quotes alone are not semantic validation. Invalid or missing outputs are not converted to zero scores.','', 'No original RAGAS scores, answer/reference records, retrieval settings or held-out files were changed. No revised evaluator is promoted automatically. Any accepted evaluator revision must be applied identically to baseline and candidate before reselecting retrieval settings.','', 'See controls.json for source pages and label rationales; results.jsonl for full prompts and outputs; summary.json for all 15 office-language cells.']
  (out/'READ_THIS_FIRST.txt').write_text('\n'.join(text),encoding='utf-8')
  assert sha(out/'controls.json')==protocol['controls_sha256']
  write(out/'hashes.json',{p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name not in ('hashes.json','judge.lock')})
  state=ROOT/'experiments/t06-t07-current-status';d=read(state/'status.json');d.update(updated=datetime.datetime.now().isoformat(),t07='Offline evaluator calibration completed; review required, no promotion or freeze',calibration_report=str(out/'READ_THIS_FIRST.txt'));write(state/'status.json',d)
  log('Calibration finished. No evaluator or pipeline promoted.')
 finally:lock.unlink()
if __name__=='__main__':main()
