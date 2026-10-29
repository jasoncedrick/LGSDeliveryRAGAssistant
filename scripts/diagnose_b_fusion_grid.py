"""Development retrieval diagnostics only; never selects weights using Hit/MRR."""
import csv
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    import numpy as np
    from src.chunk_retriever import ChunkRetriever,min_max_normalize
    from src.development_retrieval_metrics import ranking_metrics
    from scripts.evaluate_b_fidelity_candidate import read,lines,sha
    source=ROOT/'experiments/b-dictionary-bayad-development-20261029-v1'
    out=ROOT/'experiments/b-fusion-diagnostics-20261029-v1'
    if out.exists():raise ValueError('Use a fresh diagnostic version')
    norms=lines(source/'candidate_normalizations.jsonl')
    lookup={(r['configuration'],r['record_id']):r for r in norms}
    assert len(lookup)==len(norms)==180
    groups=read(ROOT/'experiments/t06-formal-development-validation-v4/development_groups.derived.json')
    assert len(groups)==30 and all(g['split']=='development' for g in groups)
    gridroot=ROOT/'experiments/t07-development-grid-format-retry-v2'
    grid=read(gridroot/'protocol.json')['weight_grid']
    art=ROOT/'experiments/chapter3-table-repaired-development-v1'
    r=ChunkRetriever.from_files(corpus_path=art/'corpus.json',bm25_path=art/'bm25_index.pkl',faiss_path=art/'faiss_index.bin',manifest_path=art/'pipeline_manifest.json')
    ids=[c['chunk_id'] for c in r.chunks]
    out.mkdir()
    protocol={'held_out_accessed':False,'weights':grid,'k':[3,5],'source_sha256':sha(source/'candidate_normalizations.jsonl'),
        'artifact_hashes':r.artifact_hashes,'selection_objective':'Chapter 3: macro RAGAS context precision across 15 office-language cells',
        'selection_status':'NOT_SELECTED: Hit/MRR diagnostics only; semantic failures remain; no new judge run',
        'dictionary_definition_changes_affect_boost':False,'note':'Boost uses dictionary keys, which are unchanged. Same weights and dictionary scoring for B and C.'}
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8')
    cache={};rows=[]
    for c in 'BC':
        records=lines(ROOT/f'experiments/t07-development-abc-v1/{c}/interactions.jsonl')
        assert len(records)==90 and {x['question_group_id'] for x in records}=={g['group_id'] for g in groups}
        for ix,x in enumerate(records,1):
            n=lookup[c,x['record_id']]['normalization'];q=n.get('normalized_query');matrix=None
            if n['status']=='SUCCESS' and q:
                if q not in cache:
                    sparse=np.asarray(r.bm25.get_scores(q.lower().split()),dtype=float)
                    emb=np.asarray(r.embedder.encode([q],normalize_embeddings=True),dtype=np.float32)
                    dist,indices=r.index.search(emb,len(ids));dense=np.empty(len(ids));dense[indices[0]]=dist[0]
                    terms=[t for t in r.terms if t in q.lower()]
                    boost=np.asarray([sum(t in text for t in terms) for text in r.texts_lower])
                    cache[q]=np.column_stack([min_max_normalize(v) for v in [sparse,dense,boost]])
                matrix=cache[q]
            for gi,w in enumerate(grid):
                selected=[ids[int(i)] for i in np.argsort(-(matrix@np.asarray(w)),kind='stable')[:5]] if matrix is not None else []
                for k in [3,5]:rows.append({'configuration':c,'record_id':x['record_id'],'pillar':x['pillar'],'language':x['language'],'grid_id':gi,'k':k,**ranking_metrics(selected,x['ground_truth_chunk_ids'],k)})
            print(f'{c} {ix}/90 grid diagnostics',flush=True)
    summaries=[]
    for c in 'BC':
        for gi,w in enumerate(grid):
            for k in [3,5]:
                subset=[x for x in rows if (x['configuration'],x['grid_id'],x['k'])==(c,gi,k)]
                assert len(subset)==90
                summaries.append({'configuration':c,'grid_id':gi,'weights':json.dumps(w),'k':k,'queries':90,
                    'hit_at_k':sum(x['hit_at_k'] for x in subset)/90,'mrr_at_k':sum(x['mrr_at_k'] for x in subset)/90,'selected':False})
    for name,data in [('per_query.csv',rows),('summary.csv',summaries)]:
        with (out/name).open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(data[0]));writer.writeheader();writer.writerows(data)
    (out/'README.txt').write_text('All 17 registered weight settings and K=3/5 tested for both B/C across 90 development queries. No weights selected: Hit/MRR are diagnostics, not the Chapter 3 context-precision objective. Semantic normalization failures remain a promotion blocker. No answer generation or judge calls were made.\n',encoding='utf-8')
    print('Complete: 68 conditions, no selection or promotion.')


if __name__=='__main__':main()
