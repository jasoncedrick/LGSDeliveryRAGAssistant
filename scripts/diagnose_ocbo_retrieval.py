"""Read-only score diagnosis with fresh development probes; no tuning or benchmarks."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    import torch
    import numpy as np
    from app.pipeline import Pipeline
    from src.chunk_retriever import min_max_normalize
    directory=ROOT/'experiments/chapter3-table-repaired-development-v1'
    output=ROOT/'experiments/ocbo-retrieval-diagnosis'
    if output.exists():
        raise ValueError('Preserve previous diagnostics')
    pipeline=Pipeline(artifacts_dir=directory)
    r=pipeline.retriever
    probes=[
        ('original','OCBO-PDF0014','How long does OCBO take to encode and receive documents?'),
        ('service_explicit','OCBO-PDF0014','For an occupancy permit, how long does OCBO take to encode and receive documents?'),
        ('action_literal','OCBO-PDF0014','Encode and receive documents processing time'),
        ('original','OCBO-PDF0015','How long is the OCBO structural inspection and assessment?'),
        ('service_explicit','OCBO-PDF0015','For an occupancy permit, how long is the structural inspection and assessment?'),
        ('action_literal','OCBO-PDF0015','Structural inspection category processing time'),
    ]
    reports=[]
    for kind,target,query in probes:
        sparse=np.asarray(r.bm25.get_scores(query.lower().split()))
        vector=np.asarray(r.embedder.encode([query],normalize_embeddings=True),dtype=np.float32)
        distances,indices=r.index.search(vector,len(r.chunks))
        dense=np.empty(len(r.chunks));dense[indices[0]]=distances[0]
        terms=[term for term in r.terms if term in query.lower()]
        boost=np.asarray([sum(term in text for term in terms) for text in r.texts_lower])
        normalized=np.column_stack([min_max_normalize(x) for x in (sparse,dense,boost)])
        fused=normalized@r.weights
        orders=[np.argsort(-x,kind='stable') for x in (sparse,dense,fused)]
        ranks=[]
        for order in orders:
            rank=np.empty(len(order),dtype=int);rank[order]=np.arange(1,len(order)+1);ranks.append(rank)
        def describe(i):
            c=r.chunks[int(i)]
            return {'chunk_id':c['chunk_id'],'page':c['source_page_id'],'text':c['text_content'],
                    'bm25_raw':float(sparse[i]),'dense_raw':float(dense[i]),'fused_score':float(fused[i]),
                    'bm25_rank':int(ranks[0][i]),'dense_rank':int(ranks[1][i]),'fused_rank':int(ranks[2][i])}
        targets=[i for i,c in enumerate(r.chunks) if c['source_page_id']==target]
        best=min(int(ranks[2][i]) for i in targets)
        runtime=r.retrieve(query,top_k=5)
        assert runtime['source_chunk_ids']==[r.chunks[int(i)]['chunk_id'] for i in orders[2][:5]]
        reports.append({'kind':kind,'query':query,'target_page':target,'best_target_page_rank':best,
                        'hit_at_3':best<=3,'hit_at_5':best<=5,
                        'targets':[describe(i) for i in targets],'top_10':[describe(i) for i in orders[2][:10]]})
    output.mkdir()
    report={'status':'DEVELOPMENT_DIAGNOSTIC_ONLY','weights':r.weights.tolist(),'scoring_matches_runtime':True,
            'corpus_hashes':r.artifact_hashes,'probes':reports,'corpus_or_app_modified':False,'benchmarks_accessed':False,
            'limitations':'Expected-page hits are diagnostic, not answer accuracy. Original questions omit permit type; competing official services may also match.'}
    (output/'scores.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps([{k:p[k] for k in ['kind','query','best_target_page_rank','hit_at_3','hit_at_5']} for p in reports],indent=2))


if __name__=='__main__':
    main()
