"""Evidence-only manuscript drafting data and publication figures; no model calls."""
from pathlib import Path
import sys,json,csv,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tmp/manuscript-plot-deps'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
OUT=ROOT/'outputs/manuscript-closeout-20261028'
FINAL=ROOT/'experiments/t07-final-evaluation-v1'
HUMAN=ROOT/'experiments/t10-t12-human-analysis-v1'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
OUT.mkdir(parents=True,exist_ok=True);(OUT/'figures').mkdir(exist_ok=True)
old=read(FINAL/'source_span_crosswalk.v1.json');new=read(FINAL/'source_span_crosswalk.json')
assert sha(FINAL/'source_span_crosswalk.v1.json')==read(FINAL/'execution_manifest.json')['source_crosswalk_sha256']
assert sha(FINAL/'source_span_crosswalk.json')==read(FINAL/'source_span_crosswalk.seal.json')['sha256']
metrics=list(csv.DictReader((FINAL/'per_query_metrics.csv').open(encoding='utf8')))
matched=list(csv.DictReader((FINAL/'matched_metrics.csv').open(encoding='utf8')))
tables=[]
for metric in ['hit_at_k','mrr_at_k']:
    row={'metric':metric,'n':177}
    for config in 'ABC':
        archive=[json.loads(l) for l in (FINAL/config/'interactions.jsonl').read_text(encoding='utf8').splitlines()]
        eligible={r['question_id'] for r in archive if all(old['mappings'][k].get('mapped_ids') for k in r['original_ground_truth_chunk_ids'])}
        vals=[float(r[metric]) for r in metrics if r['configuration']==config and r['record_id'] in eligible]
        assert len(vals)==177;row[config]=sum(vals)/len(vals)
    tables.append(row)
for row in matched:
    # Independently recompute each matched denominator and mean from per-query CSV.
    m=row['metric'];maps={c:{r['record_id']:r for r in metrics if r['configuration']==c} for c in 'ABC'}
    good=[q for q in maps['A'] if all(maps[c][q][m] not in ('','None','nan') for c in 'ABC')]
    assert len(good)==int(row['matched_queries'])
    for c in 'ABC':assert abs(np.mean([float(maps[c][q][m]) for q in good])-float(row[c]))<1e-10
    if m not in ['hit_at_k','mrr_at_k']:tables.append({'metric':m,'n':len(good),**{c:float(row[c]) for c in 'ABC'}})
data={'primary_automated':tables,'current_reconciled_retrieval':[r for r in matched if r['metric'] in ['hit_at_k','mrr_at_k']],
      'label_reconciliation':{'original_crosswalk_sha256':sha(FINAL/'source_span_crosswalk.v1.json'),'current_crosswalk_sha256':sha(FINAL/'source_span_crosswalk.json'),'changed_mappings':[k for k in new['mappings'] if new['mappings'][k]!=old['mappings'].get(k)],'note':'Execution-manifest crosswalk resolves 77/87 spans, 177 queries. Current revised crosswalk resolves 87/87, 210 queries. Current completion assessment retains stale 177-query source-limit prose. No source recertification performed in manuscript drafting; report both versions separately.'},
      'human':read(HUMAN/'analysis_results.json'),'coverage':read(FINAL/'completion_assessment.json')['coverage']}
write(OUT/'evidence_tables.json',data)
with (OUT/'automated_original_label_subset.csv').open('w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f,fieldnames=['metric','n','A','B','C']);w.writeheader();w.writerows(tables)
colors=['#43566b','#167d8d','#b06a35'];plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,axes=plt.subplots(1,2,figsize=(9,3.6));labels=['Hit@3','MRR@3']
for i,ax in enumerate(axes):
    vals=[tables[i][c] for c in 'ABC'];ax.bar(list('ABC'),vals,color=colors,width=.55);ax.set_ylim(0,1);ax.set_title(labels[i]+' (177 matched queries)')
    for x,y in enumerate(vals):ax.text(x,y+.025,f'{y:.3f}',ha='center')
fig.tight_layout();fig.savefig(OUT/'figures/figure_4_1_retrieval.png',dpi=300);fig.savefig(OUT/'figures/figure_4_1_retrieval.pdf');plt.close(fig)
human=data['human'];fig,axes=plt.subplots(1,3,figsize=(10,3.5))
for ax,dim,maximum in zip(axes,['fidelity','relevance','faithfulness'],[5,4,4]):
    rs=[r for r in human['descriptives'] if r['dimension']==dim and r['language']=='all']
    ax.bar([r['configuration'] for r in rs],[r['mean'] for r in rs],color=[colors['ABC'.index(r['configuration'])] for r in rs],width=.55)
    ax.set_ylim(0,maximum);ax.set_title(dim.capitalize()+f' (1-{maximum})');ax.set_ylabel('Mean score')
    for i,r in enumerate(rs):ax.text(i,r['mean']+.07,f"{r['mean']:.3f}",ha='center')
fig.tight_layout();fig.savefig(OUT/'figures/figure_4_2_human_means.png',dpi=300);fig.savefig(OUT/'figures/figure_4_2_human_means.pdf');plt.close(fig)
fig,ax=plt.subplots(figsize=(8.5,3.1));rs=human['reliability'];ys=np.arange(3)
ax.errorbar([r['ordinal_alpha'] for r in rs],ys,xerr=[[r['ordinal_alpha']-r['ci95_low'] for r in rs],[r['ci95_high']-r['ordinal_alpha'] for r in rs]],fmt='o',capsize=5,color=colors[1])
ax.set_yticks(ys,[r['module']+' '+r['dimension'] for r in rs]);ax.set_xlim(.7,1);ax.axvline(.8,color='#8c3a3a',linestyle='--',label='Target .80');ax.set_xlabel('Ordinal alpha with 95% scenario-bootstrap interval');ax.legend(loc='lower right');fig.tight_layout();fig.savefig(OUT/'figures/figure_4_3_agreement.png',dpi=300);fig.savefig(OUT/'figures/figure_4_3_agreement.pdf');plt.close(fig)
write(OUT/'source_manifest.json',{'date':'2026-10-28','files':{str(p.relative_to(ROOT)):sha(p) for p in [FINAL/'matched_metrics.csv',FINAL/'per_query_metrics.csv',FINAL/'source_span_crosswalk.v1.json',FINAL/'source_span_crosswalk.json',FINAL/'execution_manifest.json',FINAL/'candidate_registration.json',HUMAN/'analysis_results.json',HUMAN/'analysis_plan.json']},'manuscript_sha256':sha(Path('D:/thesis/20260923.pdf')),'computed_tables_verified':True})
print('Evidence tables reconciled and three figures created at 300 DPI plus vector PDF.')
