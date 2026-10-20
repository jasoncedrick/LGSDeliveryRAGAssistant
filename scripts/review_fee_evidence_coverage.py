"""Review source coverage and judge/reference disagreements, preserving every score."""
from pathlib import Path
import json,csv,hashlib,datetime
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'experiments'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def lines(p):return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
 out=E/'bfp002-evidence-coverage-review-v1';out.mkdir(exist_ok=True)
 grid=E/'punctuation-context-precision-format-retry-v2';inputs=[grid/n for n in ['context_precision_grid.json','judge_verdicts.jsonl','rankings.jsonl','protocol.json']]
 inputs += [E/'t06-formal-development-validation-v4/development_groups.derived.json',E/'chapter3-table-repaired-development-v1/corpus.json']
 hashes={str(p.relative_to(ROOT)):sha(p) for p in inputs}
 weights=read(grid/'protocol.json')['weight_grid'];result=read(grid/'context_precision_grid.json');objective={(r['grid_id'],r['k']):r['J'] for r in result['results']};best=result['best_complete_candidate'];rows=lines(grid/'rankings.jsonl')
 chunks={r['chunk_id']:r for r in read(E/'chapter3-table-repaired-development-v1/corpus.json')};groups=read(E/'t06-formal-development-validation-v4/development_groups.derived.json');assert len(groups)==30 and all(g['split']=='development' for g in groups)
 refs={g['group_id']:g for g in groups};targets={'DEV120-BFP-PDF0001-C019','DEV120-BFP-PDF0001-C020'};coverage=[]
 for row in rows:
  if row['configuration']!='B' or not row['record_id'].startswith('SCENARIO-BFP-002-'):continue
  for k in [3,5]:
   retrieved=row['rankings'][str(k)];hits=targets&set(retrieved)
   coverage.append({'record_id':row['record_id'],'grid_id':row['grid_id'],'weights':weights[row['grid_id']],'k':k,'J':objective[row['grid_id'],k],'formula_found':'DEV120-BFP-PDF0001-C019' in hits,'zero_exception_found':'DEV120-BFP-PDF0001-C020' in hits,'both_evidence_chunks_found':hits==targets,'retrieved_ids':retrieved})
 write(out/'fee_grid_coverage.json',coverage)
 verdicts={(r['record_id'],r['chunk_id']):r for r in lines(grid/'judge_verdicts.jsonl')}
 selected=[r for r in rows if r['configuration']=='B' and r['grid_id']==best['grid_id']];assert len(selected)==90
 flags=[];case=[]
 for row in selected:
  ids=row['rankings'][str(best['k'])];rid=row['record_id'];group=refs[rid.rsplit('-',1)[0]];hits=set(ids)&set(group['ground_truth_chunk_ids']);positive=[cid for cid in ids if verdicts[rid,cid]['parsed'] and verdicts[rid,cid]['parsed']['verdict']=='1']
  if ids and not hits and positive:flags.append({'record_id':rid,'positive_judge_count':len(positive),'judge_positive_chunk_ids':positive,'retrieved_ids':ids,'reference_chunk_ids':group['ground_truth_chunk_ids'],'status':'JUDGE_LABEL_DISCORDANCE_REQUIRES_SOURCE_COMPARISON','policy':'Gold IDs can be incomplete or overlapping; this flag alone does not prove a judge error.'})
  if rid=='SCENARIO-BFP-002-taglish':
   for cid in ids:
    v=verdicts[rid,cid]
    case.append({'chunk_id':cid,'source_text':chunks[cid]['text_content'],'judge_verdict':v['parsed'],'source_review':'No FSIF calculation, minimum amount or zero-assessment exception appears in this chunk. Judge rationale claims or infers these facts despite their absence.','review_basis':'Assistant direct comparison of the complete retrieved chunk with the stored rationale, supported by the user-confirmed fee panel; not an independent expert rating.'})
 write(out/'selected_query_judge_label_discordance.json',flags);write(out/'bfp002_taglish_judge_source_comparison.json',case)
 summary={'selected_weights':weights[best['grid_id']],'selected_k':best['k'],'candidate_J':best['J'],'taglish_grid_conditions':sum(r['record_id']=='SCENARIO-BFP-002-taglish' for r in coverage),'taglish_conditions_retrieving_both':sum(r['record_id']=='SCENARIO-BFP-002-taglish' and r['both_evidence_chunks_found'] for r in coverage),'by_language':{lang:{'conditions':sum(r['record_id'].endswith('-'+lang) for r in coverage),'both_found':sum(r['record_id'].endswith('-'+lang) and r['both_evidence_chunks_found'] for r in coverage)} for lang in ['english','taglish','bislish']},'selected_90_query_discordance_flags':len(flags),'confirmed_taglish_unsupported_judge_positives':sum(r['judge_verdict']['verdict']=='1' for r in case),'decision':'HOLD_PROMOTION_AND_FREEZE_PENDING_EVALUATOR_CALIBRATION','next_step':'Calibrate offline Context Precision judging with predeclared positive/negative evidence controls across all five service categories; apply any evaluator revision consistently to baseline and candidate before comparing objectives. Do not change the live response pipeline or substitute Hit Rate for the manuscript objective.','held_out_accessed':False,'original_scores_changed':False,'app_defaults_changed':False,'independent_expert_certification':False}
 write(out/'summary.json',summary)
 text=['EVIDENCE COVERAGE AND EVALUATOR REVIEW','',f"Decision: {summary['decision']}",'',f"BFP-002 Taglish: {summary['taglish_conditions_retrieving_both']} of 34 grid conditions retrieve both formula and exception chunks.",f"Selected candidate: weights {summary['selected_weights']}, K={best['k']}, J={best['J']:.9f}",f"All {summary['confirmed_taglish_unsupported_judge_positives']} selected Taglish chunks are marked useful by the judge even though they do not state the requested fee formula or exception.",'The stored rationales repeat reference-answer fee facts absent from the retrieved chunks. This is an observed source-grounding error, not proof of the model mechanism causing it.','',f"Across the full 90-query selected candidate, {len(flags)} queries have at least one judge-positive chunk but no overlap with the reference IDs. These are review flags, not confirmed errors: other valid source evidence can exist outside the saved IDs.",'','What remains unchanged','All source chunks, original query texts, reference answers, relevance labels, numeric automated scores and judge traces remain preserved. No source transcription repair is indicated for the two fee chunks.','', 'Recommended next action',summary['next_step'],'Declare calibration labels and format criteria before looking at new judge outputs. Save all raw requests and responses. Treat invalid output as missing rather than zero. Preserve the original evaluation alongside any revised evaluator run.','The same evaluator must score competing configurations; do not repair only one candidate or use final held-out questions for calibration.','Manual expert review can supplement this audit, but has not been completed or fabricated here. No new source clarification is requested from the user for BFP-002.','', 'Methodology alignment','Chapter 3.1 and Figure 2, PDF24-25: evaluation remains offline; no serving critic or regeneration chain is added.','Chapter 3.2.7, PDF33: Context Precision across 15 office-language cells remains the declared tuning objective. Judge unreliability is documented rather than replacing it with a favorable metric.','Chapter 3.2.8, PDF34: held-out set remains isolated; freeze is postponed.','T06 remains the implemented evaluation harness. This evidence does not complete the frozen T07 comparison.','', 'Read bfp002_taglish_judge_source_comparison.json for the exact texts and rationales, fee_grid_coverage.json for all 102 language/weight/K conditions, and selected_query_judge_label_discordance.json for the wider review queue.']
 (out/'READ_THIS_FIRST.txt').write_text('\n'.join(text),encoding='utf-8')
 assert all(sha(ROOT/p)==h for p,h in hashes.items())
 write(out/'input_hashes.json',hashes)
 state=E/'t06-t07-current-status';status=read(state/'status.json');status.update(updated=datetime.datetime.now().isoformat(),t07=summary['decision'],evidence_review=str(out/'READ_THIS_FIRST.txt'),held_out_accessed=False,app_defaults_changed=False);write(state/'status.json',status)
 with (state/'READ_THIS_FIRST.txt').open('a',encoding='utf-8') as f:f.write('\n\nEVIDENCE COVERAGE REVIEW\nexperiments/bfp002-evidence-coverage-review-v1/READ_THIS_FIRST.txt\nHOLD promotion and freeze. Calibrate the offline evaluator before interpreting the small objective improvement. Original scores are preserved.\n')
 write(out/'hashes.json',{p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='hashes.json'})
 print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
