"""Ranking metrics for explicit development relevance IDs (not RAGAS metrics)."""


def ranking_metrics(retrieved_ids, relevant_ids, k):
    if k not in (3,5):
        raise ValueError('Chapter 3 K must be 3 or 5')
    relevant=set(relevant_ids)
    if not relevant:
        raise ValueError('Missing relevance labels; do not count as a retrieval miss')
    selected=list(retrieved_ids)[:k]
    if len(selected)!=len(set(selected)):
        raise ValueError('Duplicate retrieved IDs')
    first=next((i for i,cid in enumerate(selected,1) if cid in relevant),None)
    return {'hit_at_k':int(first is not None),'mrr_at_k':1/first if first else 0.0}
