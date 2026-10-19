"""Resume exact-prompt cached RAGAS context-precision judging for the declared grid."""
import json,hashlib,time,copy,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ['RAGAS_DO_NOT_TRACK']='true'
import sys
sys.path.insert(0,str(ROOT))
def main():
 # Serialize local model work behind the active full T06 scoring process.
 ready=ROOT/'experiments/t06-ragas-reviewed-development-v2/summary.json'
 while not ready.exists():time.sleep(10)
 from ragas.metrics import context_precision
 from langchain_community.llms import Ollama
 from src.ragas_output_contracts import apply_contracts
 m=copy.deepcopy(context_precision);apply_contracts({'context_precision':m})
 judge=Ollama(model='eboss-mistral',base_url='http://localhost:11434',temperature=0,top_p=0,num_ctx=8192,num_predict=1024,num_thread=4,timeout=90)
 out=ROOT/'experiments'/os.environ.get('T07_GRID_DIRECTORY','t07-development-grid-v1');source=ROOT/'experiments/t06-formal-development-validation-v4/interactions.corrected_references.jsonl';records={r['record_id']:r for r in [json.loads(l) for l in source.read_text(encoding='utf-8').splitlines()]};chunks={c['chunk_id']:c['text_content'] for c in json.loads((ROOT/'experiments/chapter3-table-repaired-development-v1/corpus.json').read_text(encoding='utf-8'))};rankings=[json.loads(l) for l in (out/'rankings.jsonl').read_text(encoding='utf-8').splitlines() if json.loads(l)['configuration']=='B'];pairs=sorted({(r['record_id'],c) for r in rankings for c in r['rankings']['5']})
 cache={};cachefile=out/'judge_verdicts.jsonl'
 if cachefile.exists():
  for l in cachefile.read_text(encoding='utf-8').splitlines():
   x=json.loads(l);cache[x['prompt_sha256']]=x
 # Import only exact prompt/response matches from completed T06 trace; no score-level blending.
 trace=ROOT/'experiments/t06-ragas-reviewed-development-v2/judge_calls.jsonl';pending=[];traces={}
 for l in trace.read_text(encoding='utf-8').splitlines():
  x=json.loads(l)
  if x['event']=='judge_prompt':pending=x['prompts']
  elif x['event']=='judge_output':
   outputs=[g[0] for g in x['outputs'] if g]
   if len(outputs)==len(pending):
    for prompt,answer in zip(pending,outputs):traces[hashlib.sha256(prompt.encode()).hexdigest()]=answer
   pending=[]
 def parse(raw):
  try:
   x=json.loads(raw)
   return x if isinstance(x,dict) and isinstance(x.get('reason'),str) and x.get('verdict') in ('0','1') else None
  except (ValueError,TypeError):return None
 verdicts={}
 for number,(rid,cid) in enumerate(pairs,1):
  r=records[rid];prompt=m._context_precision_prompt({'question':r['question'],'contexts':[chunks[cid]],'ground_truth':r['reference_answer']})[0].to_string();key=hashlib.sha256(prompt.encode()).hexdigest()
  item=cache.get(key)
  if not item:
   raw=traces.get(key);origin='exact_T06_prompt_cache' if raw is not None else 'new_judge_call'
   try:
    if raw is None:raw=judge.invoke(prompt)
    parsed=parse(raw);item={'record_id':rid,'chunk_id':cid,'prompt_sha256':key,'prompt':prompt,'raw_output':raw,'parsed':parsed,'origin':origin,'status':'SCORED' if parsed else 'FORMAT_FAILURE'}
   except Exception as e:item={'record_id':rid,'chunk_id':cid,'prompt_sha256':key,'prompt':prompt,'parsed':None,'origin':origin,'status':'SCORING_ERROR','error':str(e)}
   with cachefile.open('a',encoding='utf-8') as f:f.write(json.dumps(item,ensure_ascii=False)+'\n')
   cache[key]=item
  verdicts[(rid,cid)]=item['parsed'];(out/'judge_progress.json').write_text(json.dumps({'completed':number,'total':len(pairs),'latest_status':item['status']}),encoding='utf-8')
  print(number,len(pairs),item['status'],flush=True)
 results=[]
 for grid in sorted({r['grid_id'] for r in rankings}):
  for k in [3,5]:
   cells={};failures=0
   for row in [x for x in rankings if x['grid_id']==grid]:
    r=records[row['record_id']];ids=row['rankings'][str(k)];v=[verdicts[(row['record_id'],c)] for c in ids]
    score=0.0 if not ids else (float(m._calculate_average_precision(v)) if all(x is not None for x in v) else None)
    failures+=score is None;cells.setdefault(r['pillar']+'|'+r['language'],[]).append(score)
   assert len(cells)==15 and all(len(v)==6 for v in cells.values())
   means={c:sum(v)/len(v) if all(x is not None for x in v) else None for c,v in cells.items()};objective=sum(means.values())/15 if all(v is not None for v in means.values()) else None
   results.append({'grid_id':grid,'k':k,'J':objective,'cell_means':means,'judge_failed_queries':failures})
 eligible=[r for r in results if r['J'] is not None];best=max(eligible,key=lambda r:r['J']) if eligible else None
 (out/'context_precision_grid.json').write_text(json.dumps({'results':results,'best_complete_candidate':best,'selection_status':'READY_FOR_COMPARISON_NOT_FROZEN' if best and len(eligible)==len(results) else 'INCOMPLETE_JUDGING_NO_FINAL_SELECTION','coverage_policy':'No-context stopped queries zero; judge errors null, never zero. Candidate selection final only when every grid cell is scored.','held_out_accessed':False},indent=2),encoding='utf-8')
if __name__=='__main__':main()
