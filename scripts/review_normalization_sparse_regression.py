"""Summarize full development factorial regression without selecting on Hit/MRR."""
from pathlib import Path
import json,csv,hashlib,datetime,collections
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=ROOT/'experiments/normalization-sparse-development-regression-v1';summary=json.loads((p/'summary.json').read_text(encoding='utf-8'));results=summary['results']
 with (p/'per_query_metrics.csv').open(encoding='utf-8') as f:rows=list(csv.DictReader(f))
 details=[json.loads(l) for l in (p/'rankings.jsonl').read_text(encoding='utf-8').splitlines()]
 lookup={(r['configuration'],r['normalization'],r['sparse_tokenizer'],r['record_id'],int(r['k'])):r for r in rows}
 deltas=[]
 for config in 'BC':
  for version,mode in [('archived','punctuation'),('candidate','whitespace'),('candidate','punctuation')]:
   for k in [3,5]:
    for r in [r for r in rows if r['configuration']==config and r['normalization']==version and r['sparse_tokenizer']==mode and int(r['k'])==k]:
     b=lookup[config,'archived','whitespace',r['record_id'],k]
     deltas.append({'configuration':config,'normalization':version,'sparse_tokenizer':mode,'k':k,'record_id':r['record_id'],'hit_delta':float(r['hit_at_k'])-float(b['hit_at_k']),'mrr_delta':float(r['mrr_at_k'])-float(b['mrr_at_k']),'baseline_status':b['status'],'candidate_status':r['status']})
 with (p/'query_deltas.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(deltas[0]));w.writeheader();w.writerows(deltas)
 bycell=[]
 for config,version,mode,k in sorted({(r['configuration'],r['normalization'],r['sparse_tokenizer'],int(r['k'])) for r in rows}):
  cells=collections.defaultdict(list)
  for r in rows:
   if (r['configuration'],r['normalization'],r['sparse_tokenizer'],int(r['k']))==(config,version,mode,k):cells[r['pillar']+'|'+r['language']].append(r)
  assert len(cells)==15 and all(len(v)==6 for v in cells.values())
  for cell,rs in cells.items():bycell.append({'configuration':config,'normalization':version,'sparse_tokenizer':mode,'k':k,'cell':cell,'n':6,'hit_at_k':sum(float(r['hit_at_k']) for r in rs)/6,'mrr_at_k':sum(float(r['mrr_at_k']) for r in rs)/6})
 with (p/'office_language_metrics.csv').open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=list(bycell[0]));w.writeheader();w.writerows(bycell)
 text=['NORMALIZATION AND BM25 DEVELOPMENT REGRESSION REVIEW','',f'Completed {datetime.datetime.now().isoformat()}','Scope: unchanged 30 development groups, 90 original queries per configuration; no held-out access.','',
 'Diagnosis: BFP formula chunk is dense rank 1, sparse rank 470, fused rank 177 under archived B. The exception is dense rank 15, sparse rank 606, fused rank 315. Only stopword-like query tokens match the formula under whitespace BM25. Acronym punctuation, wording variation and the missing FSIC reduce lexical evidence; full source phrases are not present in each chunk.','',
 'Four conditions isolate archived/candidate normalization and whitespace/punctuation BM25. B and C both use .75/.25/0 fusion at K=3 and K=5. A uses raw queries and sparse retrieval only. Original archived top-3 rankings were reproduced for all configurations before comparisons. Numeric BM25 parameters and corpus windows remain unchanged.','',
 'FULL 90-QUERY DIAGNOSTICS']
 for r in results:
  text.append(f"{r['configuration']} {r['normalization']} {r['sparse_tokenizer']} K={r['k']}: Hit={r['hit_at_k']:.4f} MRR={r['mrr_at_k']:.4f}; statuses={r['statuses']}; fidelity-error queries={r['queries_with_fidelity_errors']}")
 text+=['','BFP-002 TAGLISH FEE-PANEL RANKS']
 for d in details:
  if d['record_id']=='SCENARIO-BFP-002-taglish':text.append(f"{d['configuration']} {d['normalization']} {d['sparse_tokenizer']}: {d['status']}; query={d['query']}; ranks={d.get('fee_chunk_ranks',{})}")
 text+=['','REVIEW DECISION','No candidate is promoted or frozen. Hit/MRR are diagnostics, not the manuscript weight-selection objective. New rankings require RAGAS Context Precision across all 15 office-language cells before weight selection.','If the retrieval candidate is retained, build a separately versioned matching sparse index and protocol, validate corpus/index alignment and app integration, then repeat paired development answer generation and offline scoring. Current app and baseline artifacts were not changed.','A higher Hit score does not show that every fee condition or exception is retrieved. Check C019 (formula) and C020 (zero-assessment exception) separately; ranking either one alone does not establish complete answer evidence.','Fidelity checks cover output shape, truncation and supplied acronyms. They do not certify semantic equivalence, role direction or every numerical qualifier. Candidate errors are retained and counted as no retrieval, distinct from the unchanged ambiguity gate.','Archived normalizations are the baseline; candidate normalizations were freshly generated. Differences are not proof of a causal prompt effect or statistical significance. Shared static lexical guidance remains in C.','No new source transcription check is needed for this BFP fee panel: the user image and corpus wording agree. Human review remains necessary before claiming expert certification.','', 'FILES','summary.csv: all conditions and both K values','query_deltas.csv: wins/losses for every query versus its archived baseline','office_language_metrics.csv: all 15 cells, six records per cell','candidate_normalizations.jsonl: original model outputs and explicit fidelity failures','rankings.jsonl: actual ranked chunk IDs','protocol.json and hashes.json: configuration and input provenance']
 fidelity=[]
 norms={(r['configuration'],r['record_id']):r for r in [json.loads(l) for l in (p/'candidate_normalizations.jsonl').read_text(encoding='utf-8').splitlines()]}
 for config in 'BC':
  originals=[json.loads(l) for l in (ROOT/f'experiments/t07-development-abc-v1/{config}/interactions.jsonl').read_text(encoding='utf-8').splitlines()]
  for version in ['archived','candidate']:
   changed=[];eligible=0
   for r in originals:
    n=r['normalization'] if version=='archived' else norms[config,r['record_id']]['normalization']
    if r['language']=='english' and n.get('status')=='SUCCESS':
     eligible+=1
     if n.get('normalized_query')!=r['question']:changed.append(r['record_id'])
   fidelity.append({'configuration':config,'normalization':version,'English_success_queries':eligible,'English_exact_copy_failures':len(changed),'changed_record_ids':changed,'interpretation':'Exact-string diagnostic against the shared prompt copy instruction; changes need not all be semantic errors.'})
 (p/'english_copy_fidelity.json').write_text(json.dumps(fidelity,indent=2),encoding='utf-8')
 text+=['','ENGLISH COPY FIDELITY']+[f"{r['configuration']} {r['normalization']}: {r['English_exact_copy_failures']} changed of {r['English_success_queries']} successful English queries. Exact changes are not necessarily semantic errors, but violate the current exact-copy prompt instruction." for r in fidelity]
 (p/'REVIEW_RESULTS.txt').write_text('\n'.join(text),encoding='utf-8')
 state=ROOT/'experiments/t06-t07-current-status';(state/'status.json').write_text(json.dumps({'updated':datetime.datetime.now().isoformat(),'t06':'COMPLETE_DEVELOPMENT_VALIDATED_HARNESS','t07':'Full 90-query normalization and BM25 regression complete; candidate not promoted or frozen','review_report':str(p/'REVIEW_RESULTS.txt'),'held_out_accessed':False,'app_defaults_changed':False},indent=2),encoding='utf-8')
 with (state/'READ_THIS_FIRST.txt').open('a',encoding='utf-8') as f:f.write('\n\nLATEST DEVELOPMENT REGRESSION: experiments/normalization-sparse-development-regression-v1/REVIEW_RESULTS.txt\nAll 90 queries tested per condition; no candidate promoted or frozen. New-ranked contexts need Context Precision evaluation before selection.\n')
 (p/'hashes.json').write_text(json.dumps({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in p.iterdir() if f.is_file() and f.name!='hashes.json'},indent=2),encoding='utf-8')
 print('\n'.join(text))
if __name__=='__main__':main()
