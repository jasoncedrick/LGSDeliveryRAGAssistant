"""Review the candidate grid once offline judging finishes; never deploy or freeze."""
from pathlib import Path
import argparse,json,hashlib,time,datetime
ROOT=Path(__file__).resolve().parents[1]
def main(wait=False):
 out=ROOT/'experiments/punctuation-context-precision-v1';result=out/'baseline_comparison.json'
 while wait and not result.exists():time.sleep(10)
 comparison=json.loads(result.read_text(encoding='utf-8'));grid=json.loads((out/'context_precision_grid.json').read_text(encoding='utf-8'));protocol=json.loads((out/'protocol.json').read_text(encoding='utf-8'))
 complete=grid['selection_status']=='READY_FOR_COMPARISON_NOT_FROZEN';assert len(grid['results'])==34
 assert all(len(r['cell_means'])==15 for r in grid['results'])
 best=grid['best_complete_candidate'];baseline=comparison['baseline_best'];weights=protocol['weight_grid'][best['grid_id']] if best else None
 rows=[json.loads(l) for l in (out/'rankings.jsonl').read_text(encoding='utf-8').splitlines()]
 fee=next((r['rankings'][str(best['k'])] for r in rows if best and r['configuration']=='B' and r['grid_id']==best['grid_id'] and r['record_id']=='SCENARIO-BFP-002-taglish'),[])
 fee_coverage={cid:cid in fee for cid in ['DEV120-BFP-PDF0001-C019','DEV120-BFP-PDF0001-C020']}
 decision='INCOMPLETE_JUDGING_REQUIRES_FAILURE_REVIEW'
 if complete:decision='OBJECTIVE_IMPROVEMENT_REQUIRES_PAIRED_DEVELOPMENT_GENERATION' if best['J']>baseline['J']+1e-9 else 'NO_MEANINGFUL_OBJECTIVE_IMPROVEMENT_DO_NOT_PROMOTE'
 review={'decision':decision,'grid_complete':complete,'candidate_weights':weights,'candidate_k':best['k'] if best else None,'candidate_J':best['J'] if best else None,'baseline_J':baseline['J'],'objective_difference':comparison.get('J_difference'),'fee_case_top_k':fee,'fee_evidence_coverage':fee_coverage,'held_out_accessed':False,'app_defaults_changed':False,'freeze':False,'limits':['Local LLM judge has documented semantic errors; parse success is not human certification.','Archived normalization is unchanged and retains documented acronym and paraphrasing problems.','C retains shared static lexical guidance.','A higher Context Precision objective does not establish complete fee/exception evidence.','Original source wording ambiguities and detached BFP context associations remain documented.']}
 (out/'review_decision.json').write_text(json.dumps(review,indent=2),encoding='utf-8')
 text=['PUNCTUATION CANDIDATE CONTEXT PRECISION REVIEW','',f'Decision: {decision}',f'Complete grid: {complete}',f'Candidate weights [BM25, dense, dictionary]: {weights}',f"Candidate K: {review['candidate_k']}",f"Candidate J: {review['candidate_J']}",f"Baseline J: {review['baseline_J']}",f"Difference: {review['objective_difference']}",'','Objective is the Chapter 3 macro mean over all 15 office-language cells and the unchanged 90 development queries. This is separate from conditional answer-only RAGAS averages.','',f'BFP-002 Taglish fee evidence present in candidate top K: {fee_coverage}','', 'Framework alignment: METHOD_ALIGNMENT.txt','No serving filter, query-specific routing, section expansion, synthetic source text or held-out tuning was introduced.','No candidate was deployed or frozen. Further paired generation, coverage review and exact configuration registration are required before any final held-out evaluation.','', 'Limitations:']+review['limits']
 (out/'REVIEW_RESULTS.txt').write_text('\n'.join(text),encoding='utf-8')
 status=ROOT/'experiments/t06-t07-current-status/status.json';d=json.loads(status.read_text(encoding='utf-8'));d.update(updated=datetime.datetime.now().isoformat(),t07='Punctuation Context Precision run finished; '+decision,objective_review=str(out/'REVIEW_RESULTS.txt'),held_out_accessed=False,app_defaults_changed=False);status.write_text(json.dumps(d,indent=2),encoding='utf-8')
 with (status.parent/'READ_THIS_FIRST.txt').open('a',encoding='utf-8') as f:f.write('\n\nLATEST OBJECTIVE REVIEW\nexperiments/punctuation-context-precision-v1/REVIEW_RESULTS.txt\n'+decision+'\nNo deployment or freeze.\n')
 (out/'hashes.review.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file() and f.name not in ('hashes.review.json','judge.lock')},indent=2),encoding='utf-8')
 print(json.dumps(review),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--wait',action='store_true');main(p.parse_args().wait)
