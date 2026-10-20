"""Prepare the declared development grid with a separate punctuation BM25 index."""
from pathlib import Path
import sys,json,hashlib,pickle,csv
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from src.chunk_retriever import min_max_normalize,ChunkRetriever
from scripts.test_normalization_sparse_candidate import tokens
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def lines(p):return [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=ROOT/'experiments/punctuation-context-precision-v1';out.mkdir(exist_ok=True)
 if (out/'rankings.jsonl').exists():print('Prepared grid exists; preserved');return
 old=ROOT/'experiments/t07-development-grid-v1';reg=ROOT/'experiments/normalization-sparse-development-regression-v1';art=ROOT/'experiments/chapter3-table-repaired-development-v1'
 rt=ChunkRetriever.from_files(corpus_path=art/'corpus.json',bm25_path=art/'bm25_index.pkl',faiss_path=art/'faiss_index.bin',manifest_path=art/'pipeline_manifest.json')
 assert rt.artifact_hashes==read(reg/'protocol.json')['artifact_hashes']
 ids=[c['chunk_id'] for c in rt.chunks];assert ids==read(old/'chunk_order.json')
 bundle=pickle.loads((reg/'bm25_punctuation_candidate.pkl').read_bytes());assert bundle['chunks']==rt.chunks and bundle['bm25'].corpus_size==len(ids)
 weights=read(old/'protocol.json')['weight_grid'];assert len(weights)==17 and all(min(w)>=0 and abs(sum(w)-1)<1e-9 for w in weights)
 source=ROOT/'experiments/t06-formal-development-validation-v4/interactions.corrected_references.jsonl';records=lines(source);assert len(records)==90
 groups=read(source.parent/'development_groups.derived.json');assert len(groups)==30 and all(g['split']=='development' for g in groups)
 previous=np.load(old/'normalized_score_vectors.npz');rows=[];a=[]
 for r in records:
  query=r.get('search_query');matrix=None
  if r['normalization']['status']=='SUCCESS' and query:
   matrix=previous[r['record_id']].copy();matrix[:,0]=min_max_normalize(bundle['bm25'].get_scores(tokens(query)))
  for wi,w in enumerate(weights):
   selected=[ids[int(i)] for i in np.argsort(-(matrix@np.asarray(w)),kind='stable')[:5]] if matrix is not None else []
   rows.append({'configuration':'B','grid_id':wi,'weights':w,'record_id':r['record_id'],'query':query,'status':r['normalization']['status'],'rankings':{'3':selected[:3],'5':selected}})
  raw=np.asarray(bundle['bm25'].get_scores(tokens(r['question'])));selected=[ids[int(i)] for i in np.argsort(-raw,kind='stable')[:5]]
  a.append({'configuration':'A','record_id':r['record_id'],'rankings':{'3':selected[:3],'5':selected}})
 (out/'rankings.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows+a),encoding='utf-8')
 protocol={**read(old/'protocol.json'),'scope':'Punctuation BM25 candidate full development Context Precision grid; not frozen','sparse_tokenizer':bundle['tokenizer'],'sparse_candidate_sha256':sha(reg/'bm25_punctuation_candidate.pkl'),'source_sha256':sha(source),'baseline_artifact_hashes':rt.artifact_hashes,'normalization':'Archived B normalization, unchanged. Rejected prompt candidate is not used.','full_corpus_score_matrix':'Reuse hash-verified unchanged dense and boost columns; recompute sparse scores with consistent punctuation tokenizer.','grid_reference':str(old/'protocol.json'),'judge_cache_policy':'Reuse parsed valid verdicts only where prompt hash matches; exclude previous modified-prompt format retries. Retain judge errors as null.','freeze':False,'held_out_accessed':False}
 (out/'protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8')
 cache=[]
 for x in lines(ROOT/'experiments/t07-development-grid-format-retry-v2/judge_verdicts.jsonl'):
  if x['status']=='SCORED' and x.get('origin')!='format_retry' and x.get('parsed') is not None:
   assert hashlib.sha256(x['prompt'].encode()).hexdigest()==x['prompt_sha256'];cache.append(x)
 (out/'judge_verdicts.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in cache),encoding='utf-8')
 pairs={(r['record_id'],cid) for r in rows for cid in r['rankings']['5']};oldpairs={(x['record_id'],x['chunk_id']) for x in cache};new=len(pairs-oldpairs)
 validation={'queries':90,'groups':30,'grid_candidates':17,'grid_K_conditions':34,'all_15_cells_have_6_queries':True,'unique_context_pairs':len(pairs),'potential_pair_cache_hits':len(pairs&oldpairs),'potential_new_judge_calls':new,'context_precision_status':'PENDING','all_inputs_hash_verified':True,'baseline_corpus_and_FAISS_unchanged':True}
 (out/'validation.json').write_text(json.dumps(validation,indent=2),encoding='utf-8')
 (out/'METHOD_ALIGNMENT.txt').write_text('''FRAMEWORK AND METHODOLOGY ALIGNMENT
20260923.pdf PDF pages 24-25, Figure 2 and Chapter 3.1: dictionary injection, Mistral translation, hybrid retrieval, grounded generation, offline evaluation. No inline evaluator or rewrite chain added.
PDF 28, section 3.2.2: original 120-token source windows and 20-token overlaps preserved. No synthetic source content, section expansion or special service routing.
PDF 29, section 3.2.3: archived normalization retained, maximum 150 tokens and original ambiguity gate retained. The new prompt revision was rejected, not promoted.
PDF 30, section 3.2.4: rank_bm25 scores each chunk; corpus/query punctuation handling is consistent. Dense embeddings and FAISS are unchanged. Min-Max scoring and nonnegative simplex fusion remain in place.
PDF 33, section 3.2.7: same 30 development groups / 90 queries. Same declared 17 weight combinations, K=3/5. Objective J is Context Precision macro mean across 15 office-language cells, six queries per cell. Stopped queries count zero; invalid judge outputs remain null and block final grid selection.
PDF 34, section 3.2.8: no held-out reads. Corpus, dictionary, prompts, code and indices must be registered before final testing. This candidate is not frozen or deployed.
Tracker grounding: authoritative Thesis Tracker requirements archived in experiments/t06-formal-development-validation-v4/methodology_and_tracker.json. T06 is harness implementation; full T07 requires frozen A/B/C comparison. No workbook status changed.

Limits retained: C shares static lexical guidance; normalization still changes some English queries. BFP fee exception can fall outside K. Local judge can accept unsupported claims. Automated scores are not expert certification. These are review items, not grounds to conceal outputs or alter test questions.
Punctuation tokenization is an implementation revision within sparse indexing, not a new conceptual stage. It must be documented in the eventual freeze manifest and applied consistently to A, B and C.
''',encoding='utf-8')
 (out/'hashes.pre_judging.json').write_text(json.dumps({p.name:sha(p) for p in out.iterdir() if p.is_file() and p.name!='hashes.pre_judging.json'},indent=2),encoding='utf-8')
 print(json.dumps(validation),flush=True)
if __name__=='__main__':main()
