"""Trace fixed-corpus ranking changes; does not tune prompts or retrieval."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.evaluate_source_evidence_dev import covers


def main():
    import torch
    import numpy as np
    from app.pipeline import Pipeline
    from src.chunk_retriever import min_max_normalize
    output=ROOT/'experiments/query-context-investigation'
    if output.exists():raise ValueError('Preserve earlier investigation')
    baseline=ROOT/'experiments/source-evidence-development-v2'
    candidate=ROOT/'experiments/source-evidence-development-v3-normalization'
    questions=json.loads((baseline/'questions.json').read_text(encoding='utf-8'))
    normalizations={mode:{n['id']:n for n in json.loads((p/'normalizations.json').read_text(encoding='utf-8'))}
                    for mode,p in [('previous',baseline),('candidate',candidate)]}
    pipeline=Pipeline(artifacts_dir=ROOT/'experiments/chapter3-table-repaired-development-v1')
    r=pipeline.retriever
    findings=[]
    for q in questions:
        if q['kind']!='answerable':continue
        variants={'raw':q['query'],**{mode:ns[q['id']].get('normalized_query') for mode,ns in normalizations.items()}}
        row={'id':q['id'],'page':q['source_page_id'],'query':q['query'],'variants':[]}
        for mode,query in variants.items():
            if not query:continue
            sparse=np.asarray(r.bm25.get_scores(query.lower().split()))
            vector=np.asarray(r.embedder.encode([query],normalize_embeddings=True),dtype=np.float32)
            distances,ids=r.index.search(vector,len(r.chunks))
            dense=np.empty(len(r.chunks));dense[ids[0]]=distances[0]
            terms=[t for t in r.terms if t in query.lower()]
            boost=np.asarray([sum(t in text for t in terms) for text in r.texts_lower])
            fused=np.column_stack([min_max_normalize(x) for x in (sparse,dense,boost)])@r.weights
            order=np.argsort(-fused,kind='stable');ranks=np.empty(len(order),dtype=int);ranks[order]=np.arange(1,len(order)+1)
            evidence=[]
            for group in q['evidence_groups']:
                eligible=[i for i,c in enumerate(r.chunks) if c['source_page_id']==q['source_page_id'] and covers(c['text_content'],group)]
                best=min(eligible,key=lambda i:ranks[i]) if eligible else None
                evidence.append({'fragments':group,'best_rank':int(ranks[best]) if best is not None else None,
                                 'chunk_id':r.chunks[best]['chunk_id'] if best is not None else None,
                                 'text':r.chunks[best]['text_content'] if best is not None else None})
            row['variants'].append({'mode':mode,'query':query,'evidence_groups':evidence,
                                    'coverage_at_5':all(e['best_rank'] is not None and e['best_rank']<=5 for e in evidence)})
        findings.append(row)
    output.mkdir()
    (output/'rank_comparison.json').write_text(json.dumps(findings,ensure_ascii=False,indent=2),encoding='utf-8')
    for row in findings:
        print(row['id'],[(v['mode'],[e['best_rank'] for e in v['evidence_groups']]) for v in row['variants']])


if __name__=='__main__':main()
