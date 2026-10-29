"""Concise, arithmetic-only comparison of exploratory development candidates."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPT = ROOT/'experiments/b-fidelity-development-20261029-v2'
GLOSS = ROOT/'experiments/b-dictionary-bayad-development-20261029-v1'
OUT = ROOT/'outputs/b-development-review-20261029'


def read(p): return json.loads(p.read_text(encoding='utf-8'))


def main():
    OUT.mkdir(exist_ok=True)
    prompt=read(PROMPT/'summary.json')['results']; gloss=read(GLOSS/'summary.json')['results']
    results=[dict(r,candidate=r.get('version','')) for r in prompt]+[dict(r,candidate='prompt + bayad gloss') for r in gloss]
    with (OUT/'comparison.csv').open('w',encoding='utf-8',newline='') as f:
        fields=['configuration','candidate','k','queries','with_context','hit_at_k','mrr_at_k']
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(results)
    baseline=list(csv.DictReader((PROMPT/'per_query_metrics.csv').open(encoding='utf-8')))
    changed=list(csv.DictReader((GLOSS/'per_query_metrics.csv').open(encoding='utf-8')))
    old={(r['configuration'],r['record_id'],r['k']):r for r in baseline if r['version']=='archived'}
    deltas=[]
    for r in changed:
        b=old[r['configuration'],r['record_id'],r['k']]
        deltas.append({**{k:r[k] for k in ['configuration','record_id','pillar','language','k']},
            'hit_delta':float(r['hit_at_k'])-float(b['hit_at_k']),
            'mrr_delta':float(r['mrr_at_k'])-float(b['mrr_at_k'])})
    with (OUT/'query_deltas.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(deltas[0]));w.writeheader();w.writerows(deltas)
    text=['# B development experiment: measured results','',
          'Post-study exploratory development only. Original held-out results and human ratings are unchanged.',
          '', '| Configuration | Variant | K | Queries | With context | Hit@K | MRR@K |',
          '| --- | --- | ---: | ---: | ---: | ---: | ---: |']
    for r in results:
        text.append(f"| {r['configuration']} | {r['candidate']} | {r['k']} | {r['queries']} | {r['with_context']} | {r['hit_at_k']:.4f} | {r['mrr_at_k']:.4f} |")
    text+=['','## What changed','',
        '- New preservation-focused few-shot normalization prompt, applied identically to B and C. B still injects definitions; C does not.',
        '- Separate one-entry dictionary candidate: bayad, “Monetary settlement of assessed regulatory fees” → “Fee or payment”. Original definition, governance tag, polysemy flag, and disambiguation settings remain archived. Only the definition changes in the candidate copy.',
        '- Original corpus, indices, 120/20 token windows, K=3/5, generation prompt and runtime defaults are unchanged.',
        '- Partial first prompt draft stopped because it lacked the existing examples. It is preserved and excluded from comparisons.',
        '', '## Interpretation and gates','',
        'These are retrieval diagnostics, not new human ratings or proof of answer-quality superiority. All 90 queries are included; no-context outcomes remain in the denominator. No new retrieval weights have been selected.',
        'Chapter 3 requires macro context precision across the 15 department/language cells for weight selection. Hit/MRR alone cannot promote a candidate. Positive and negative changes appear in query_deltas.csv.',
        'The original held-out set has already been examined. A new confirmatory claim requires untouched scenario groups and, for revised answer-quality claims, new human ratings.',
        '', '## Evidence','',
        '- experiments/b-fidelity-development-20261029-v2/: protocol, exact inputs/hashes, original versus revised queries, traces and full metrics.',
        '- experiments/b-dictionary-bayad-development-20261029-v1/: dictionary backup, candidate, exact diff, rendered-source review, reuse provenance and full metrics.',
        '- scripts/evaluate_b_fidelity_candidate.py; scripts/evaluate_b_dictionary_gloss.py: reproducible sequential runners.',
        '- tests/test_b_fidelity_experiment.py: experiment guardrails.',
        '', 'No changes were deployed. No superiority or large improvement is guaranteed.']
    (OUT/'README.md').write_text('\n'.join(text)+'\n',encoding='utf-8')
    print('\n'.join(text[:len(results)+7]))


if __name__=='__main__':main()
