"""T10-T12 audit consolidation; no inference, imputation or outcome selection."""
from pathlib import Path
import sys, json, csv, hashlib, shutil, itertools, platform
from collections import Counter, defaultdict
import numpy as np
from scipy import stats
import scipy

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tmp/t11-analysis-deps'))
import krippendorff
SOURCE=Path(r'C:\Users\User\.codex\.chatgpt-projects\g-p-6ac6a06fa534819186f2a4eae6c3c4e6\output\reviewer-independent-assessments-corrected-20261028')
PACKETS=ROOT/'experiments/t08-t09-expert-audit-v2-triple'
OUT=ROOT/'experiments/t10-t12-human-analysis-v1'
SEED=20261028
BOOT=2000

def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf8')
def csvwrite(p,rows):
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def ordinal_manual(matrix,maximum):
    # Complete raters x units; coincidence count uses ordered coder pairs / (m-1).
    m,u=matrix.shape
    counts=np.stack([(matrix==v).sum(axis=0) for v in range(1,maximum+1)],axis=1)
    o=(counts.T@counts-np.diag(counts.sum(axis=0)))/(m-1)
    n=o.sum(axis=0);total=n.sum()
    centers=np.cumsum(n)-n/2
    distance=(centers[:,None]-centers[None,:])**2
    expected=(np.outer(n,n)-np.diag(n))/(total-1)
    denominator=(expected*distance).sum()
    return float(1-(o*distance).sum()/denominator) if denominator else None

def alpha(matrix,maximum):
    if np.unique(matrix).size<2:return None
    return float(krippendorff.alpha(reliability_data=matrix,level_of_measurement='ordinal',value_domain=np.arange(1,maximum+1)))

def exact_wilcoxon(d):
    d=np.asarray(d);d=d[d!=0]
    if len(d)==0:return dict(p_value=1.0,rank_biserial=0.0,nonzero_groups=0,statistic=0.0)
    ranks=stats.rankdata(np.abs(d));weights=np.rint(2*ranks).astype(int)
    # Enumerate all sign assignments by subset-sum dynamic programming, including ties.
    ways=np.zeros(weights.sum()+1,dtype=np.int64);ways[0]=1
    for w in weights:
        old=ways.copy();ways[w:]+=old[:-w]
    observed=abs(int(np.dot(weights,np.sign(d))))
    sums=np.arange(len(ways))*2-weights.sum()
    p=float(ways[np.abs(sums)>=observed].sum()/2**len(d))
    return dict(p_value=p,rank_biserial=float(np.dot(ranks,np.sign(d))/ranks.sum()),nonzero_groups=len(d),statistic=float(min(ranks[d>0].sum(),ranks[d<0].sum())))

def run():
    if (OUT/'analysis_results.json').exists():raise FileExistsError('Create a new version to rerun; preserve completed outputs.')
    OUT.mkdir(parents=True,exist_ok=True)
    plan={
      'date':'2026-10-28','timing':'Analysis specification recorded before this computation, after ratings and prior summaries were available; exploratory, not preregistered.',
      'provenance':'Independent expert scores as explicitly confirmed by researcher; earlier conflicting metadata preserved in input correction history. Statistics cannot establish independence.',
      'T11':'Ordinal Krippendorff alpha separately for M1 fidelity, M2 relevance and M2 faithfulness. Unit = unique output, three fixed raters. Category-stratified scenario-group bootstrap, 2000 draws, 95% percentile intervals; preserve all languages/configurations/raters in each sampled group.',
      'T12':'Average raters and languages within each scenario/configuration; 20 paired scenario units. Two-sided exact signed-rank sign enumeration with midranks for ties, discard zero differences. B-C for M1; B-A, C-A, B-C for each M2 dimension. Holm correction jointly across seven comparisons. Report group mean differences, rank-biserial effects and category-stratified group bootstrap intervals (unadjusted descriptive intervals).',
      'assumptions':'Signed-rank inference assumes independent scenario groups and symmetric group-level differences under null. Averaging ordinal scores uses numeric scale coding; sign-test sensitivity also reported. Raters treated as fixed, not a random population sample. Scenario sample is category-balanced and selected after T07.',
      'sensitivity':'M2 faithfulness: separately describe data excluding outputs flagged no_factual_claims by any reviewer. Primary analysis retains every submitted score. No policy-driven recoding.',
      'seed':SEED,'bootstrap_draws':BOOT,'alpha_target':0.8,
      'references':['20260923.pdf PDF35-36','t08-t09-expert-audit-v2-triple/CHAPTER3_AMENDMENT.md','Thesis Tracker T10-T12','https://github.com/pln-fing-udelar/fast-krippendorff','https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html'],
      'scope':'Human audit T10-T12. Existing automated T07/T12 metrics not overwritten or conflated with human scores.'}
    write(OUT/'analysis_plan.json',plan)
    print('Analysis specification saved.',flush=True)
    manifest=read(SOURCE/'manifest.json')['sha256']
    for name,h in manifest.items():assert sha(SOURCE/name)==h,name
    shutil.copytree(SOURCE,OUT/'private/input_snapshot')
    key={r['answer_id']:r for r in read(PACKETS/'private/answer_key.json')}
    rows=[];validation=[]
    for file in sorted(SOURCE.glob('R*-independent.json')):
        d=read(file);rater=d['assigned_reviewer_id'];module=d['module'];packet=read(PACKETS/f'public/{rater}-{module}/packet.json')
        assert d['source_packet']['packet_id']==packet['packet_id']
        assert d['assessment_status']=='independently_scored_as_confirmed_by_researcher'
        expected={a['answer_id']:(p,a,i+1,'XYZ'[j]) for i,p in enumerate(packet['pairs']) for j,a in enumerate(p['responses'])}
        assert len(d['records'])==len(expected)
        assert {r['answer_id'] for r in d['records']}==set(expected)
        dims={'fidelity'} if module=='M1' else {'relevance','faithfulness'}
        csvpath=file.with_suffix('.csv')
        with csvpath.open(encoding='utf-8-sig',newline='') as f:csvrows={r['answer_id']:r for r in csv.DictReader(f)}
        assert set(csvrows)==set(expected)
        for r in d['records']:
            p,a,position,side=expected[r['answer_id']]
            assert (r['query_id'],r['original_question'],r['archived_output'],r['presentation_position'],r['displayed_side'])==(p['query_id'],p['question'],a['text'],position,side)
            assert set(r['dimension_scores'])==dims
            k=key[r['answer_id']];assert k['module']==module
            for dim,score in r['dimension_scores'].items():
                assert type(score)==int and 1<=score<=(5 if module=='M1' else 4)
                assert int(csvrows[r['answer_id']][dim+'_score'])==score
                rows.append(dict(module=module,dimension=dim,rater=rater,answer_id=r['answer_id'],query_id=r['query_id'],group_id=k['group_id'],configuration=k['configuration'],language=r['language'],category=r['category'],score=score,no_factual_claims=bool(r['no_factual_claims']),source_file=file.name,evidence_note=r['specific_evidence']))
        validation.append(dict(file=file.name,sha256=sha(file),records=len(d['records']),scores=sum(len(r['dimension_scores']) for r in d['records']),status='PASS'))
    assert len(rows)==1320 and len({(r['module'],r['answer_id'],r['rater']) for r in rows})==780
    csvwrite(OUT/'private/ratings_long.csv',rows)
    write(OUT/'private/ratings_long.json',rows)
    write(OUT/'validation.json',dict(files=validation,records=780,scores=1320,missing_scores=0,duplicate_scores=0,input_manifest_verified=True,content_order_packet_csv_checks='PASS',provenance=plan['provenance']))
    print('Validated 780 records and 1320 scores across six files.',flush=True)
    groups=sorted({r['group_id'] for r in rows});assert len(groups)==20
    categories={g:next(r['category'] for r in rows if r['group_id']==g) for g in groups}
    strata=[[i for i,g in enumerate(groups) if categories[g]==c] for c in sorted(set(categories.values()))]
    assert all(len(s)==4 for s in strata)
    rng=np.random.default_rng(SEED)
    boot_indices=np.concatenate([rng.choice(s,size=(BOOT,len(s)),replace=True) for s in strata],axis=1)
    descriptors=[];reliability=[];comparisons=[];group_rows=[]
    for module,dim,maximum,configs in [('M1','fidelity',5,'BC'),('M2','relevance',4,'ABC'),('M2','faithfulness',4,'ABC')]:
        selected=[r for r in rows if r['module']==module and r['dimension']==dim]
        ids=sorted({r['answer_id'] for r in selected})
        lookup={(r['answer_id'],r['rater']):r for r in selected}
        matrix=np.array([[lookup[i,f'R{n:02d}']['score'] for i in ids] for n in range(1,4)])
        estimate=alpha(matrix,maximum);assert abs(estimate-ordinal_manual(matrix,maximum))<1e-12
        indexes=[[j for j,i in enumerate(ids) if lookup[i,'R01']['group_id']==g] for g in groups]
        boot_alpha=[alpha(matrix[:,np.concatenate([indexes[j] for j in sample])],maximum) for sample in boot_indices]
        valid=[v for v in boot_alpha if v is not None]
        low,high=np.quantile(valid,[.025,.975])
        reliability.append(dict(module=module,dimension=dim,unique_outputs=len(ids),raters=3,ordinal_alpha=estimate,ci95_low=float(low),ci95_high=float(high),point_meets_080=estimate>=.8,ci_lower_meets_080=float(low)>=.8,undefined_bootstrap_draws=BOOT-len(valid)))
        csvwrite(OUT/f'private/{module}_{dim}_matrix.csv',[dict(answer_id=i,group_id=lookup[i,'R01']['group_id'],R01=int(matrix[0,j]),R02=int(matrix[1,j]),R03=int(matrix[2,j])) for j,i in enumerate(ids)])
        for c in configs:
            for lang in ['all']+sorted({r['language'] for r in selected}):
                ss=[r for r in selected if r['configuration']==c and (lang=='all' or r['language']==lang)]
                vals=[r['score'] for r in ss];cnt=Counter(vals)
                descriptors.append(dict(module=module,dimension=dim,configuration=c,language=lang,rating_count=len(vals),unique_outputs=len({r['answer_id'] for r in ss}),mean=float(np.mean(vals)),median=float(np.median(vals)),**{'score_'+str(v):cnt[v] for v in range(1,6)}))
        totals={c:np.array([sum(r['score'] for r in selected if r['group_id']==g and r['configuration']==c) for g in groups]) for c in configs}
        denominator=6 if module=='M1' else 9
        for gidx,g in enumerate(groups):
            for c in configs:group_rows.append(dict(module=module,dimension=dim,group_id=g,category=categories[g],configuration=c,n_ratings=denominator,score_sum=int(totals[c][gidx]),mean_score=float(totals[c][gidx]/denominator)))
        for x,y in ([('B','C')] if module=='M1' else [('B','A'),('C','A'),('B','C')]):
            delta=totals[x]-totals[y];means=delta/denominator;test=exact_wilcoxon(delta)
            ci=np.quantile(means[boot_indices].mean(axis=1),[.025,.975]);nonzero=delta[delta!=0]
            signp=float(stats.binomtest(int((nonzero>0).sum()),len(nonzero),.5).pvalue) if len(nonzero) else 1.0
            comparisons.append(dict(module=module,dimension=dim,contrast=x+' minus '+y,scenario_groups=20,mean_difference=float(means.mean()),ci95_low=float(ci[0]),ci95_high=float(ci[1]),positive_groups=int((delta>0).sum()),negative_groups=int((delta<0).sum()),tied_groups=int((delta==0).sum()),sign_test_p_sensitivity=signp,**test))
        print(module,dim,'alpha',round(estimate,6),flush=True)
    order=sorted(range(len(comparisons)),key=lambda i:comparisons[i]['p_value']);adjusted=0
    for rank,i in enumerate(order):
        adjusted=max(adjusted,min(1,comparisons[i]['p_value']*(len(order)-rank)))
        comparisons[i]['holm_p_value']=adjusted;comparisons[i]['significant_holm_005']=adjusted<.05
    flagged={r['answer_id'] for r in rows if r['module']=='M2' and r['no_factual_claims']}
    sens=[]
    for c in 'ABC':
        base=[r for r in rows if r['dimension']=='faithfulness' and r['configuration']==c]
        kept=[r for r in base if r['answer_id'] not in flagged]
        sens.append(dict(configuration=c,excluded_outputs=len({r['answer_id'] for r in base if r['answer_id'] in flagged}),retained_ratings=len(kept),primary_mean=float(np.mean([r['score'] for r in base])),without_no_claim_outputs_mean=float(np.mean([r['score'] for r in kept]))))
    result=dict(reliability=reliability,comparisons=comparisons,descriptives=descriptors,no_claim_sensitivity=sens,
                versions=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__,krippendorff='0.8.2'),seed=SEED)
    write(OUT/'analysis_results.json',result)
    csvwrite(OUT/'reliability.csv',reliability);csvwrite(OUT/'paired_comparisons.csv',comparisons)
    csvwrite(OUT/'descriptive_scores.csv',descriptors);csvwrite(OUT/'no_claim_sensitivity.csv',sens)
    csvwrite(OUT/'private/scenario_aggregates.csv',group_rows)
    write(OUT/'private/input_hashes.json',dict(corrected={p.name:sha(p) for p in SOURCE.iterdir() if p.is_file()},packet_key_sha256=sha(PACKETS/'private/answer_key.json'),manuscript_sha256=sha(Path('D:/thesis/20260923.pdf')),tracker_sha256=sha(Path('C:/Users/User/Downloads/thesis_progress_tracker.xlsx')),script_sha256=sha(Path(__file__))))
    print(json.dumps({'reliability':reliability,'comparisons':comparisons},indent=2))

if __name__=='__main__':run()
