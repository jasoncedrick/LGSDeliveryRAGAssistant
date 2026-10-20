"""Visible CLI entry point with a persistent log for candidate grid scoring."""
import subprocess,sys,os,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 subprocess.run([sys.executable,'-B','scripts/prepare_punctuation_context_precision.py'],cwd=ROOT,check=True)
 out=ROOT/'experiments/punctuation-context-precision-v1';lock=out/'judge.lock'
 try:fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
 except FileExistsError:raise SystemExit('A grid judge is already running; inspect progress first.')
 os.write(fd,str(os.getpid()).encode());os.close(fd)
 try:
  env=dict(os.environ,T07_GRID_DIRECTORY=out.name,RAGAS_DO_NOT_TRACK='true',PYTHONUNBUFFERED='1')
  with (out/'console.log').open('a',encoding='utf-8') as log:
   with subprocess.Popen([sys.executable,'-B','scripts/judge_t07_development_grid.py'],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace') as process:
    for line in process.stdout:print(line,end='',flush=True);log.write(line);log.flush()
    if process.wait():raise RuntimeError('Judging failed; traces preserved. Re-run to resume exact prompt cache.')
  d=json.loads((out/'context_precision_grid.json').read_text(encoding='utf-8'));baseline=json.loads((ROOT/'experiments/t07-development-grid-format-retry-v2/context_precision_grid.json').read_text(encoding='utf-8'))
  comparison={'candidate_selection_status':d['selection_status'],'candidate_best':d['best_complete_candidate'],'baseline_best':baseline['best_complete_candidate'],'held_out_accessed':False,'freeze':False,'app_defaults_changed':False,'decision':'Review candidate coverage, judge failures and framework limitations before any promotion or paired answer regeneration.'}
  if d['best_complete_candidate'] and baseline['best_complete_candidate']:comparison['J_difference']=d['best_complete_candidate']['J']-baseline['best_complete_candidate']['J']
  (out/'baseline_comparison.json').write_text(json.dumps(comparison,indent=2),encoding='utf-8')
  (out/'hashes.post_judging.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file() and f.name not in ('hashes.post_judging.json','judge.lock')},indent=2),encoding='utf-8')
  print(json.dumps(comparison),flush=True)
 finally:lock.unlink()
if __name__=='__main__':main()
