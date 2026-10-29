"""Descriptive five-department breakdown of existing results. No inference or edits."""
import csv
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HUMAN=ROOT/'experiments/t10-t12-human-analysis-v1'
FINAL=ROOT/'experiments/t07-final-evaluation-v1'
OUT=ROOT/'outputs/department-results-review-20261029'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table(name, rows):
    with (OUT/name).open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def main():
    if OUT.exists():raise ValueError('Preserve the existing review; choose a new version before recomputing.')
    manifest=read(HUMAN/'manifest.json')['files']
    for name,expected in manifest.items():
        if sha(HUMAN/name)!=expected:raise ValueError('Human source changed: '+name)
    ratings=list(csv.DictReader((HUMAN/'private/ratings_long.csv').open(encoding='utf-8-sig')))
    key={r['answer_id']:r for r in read(ROOT/'experiments/t08-t09-expert-audit-v2-triple/private/answer_key.json')}
    scores={(r['rater'],r['answer_id'],r['dimension']):int(r['score']) for r in ratings}
    outputs=defaultdict(dict)
    for file in (HUMAN/'private/input_snapshot').glob('R*-independent.json'):
        data=read(file)
        for r in data['records']:
            for dimension,score in r['dimension_scores'].items():
                assert scores[data['assigned_reviewer_id'],r['answer_id'],dimension]==score
            if data['module']=='M2':
                k=key[r['answer_id']];q=(k['group_id'],r['language'])
                if k['configuration'] in outputs[q]:assert outputs[q][k['configuration']]==r['archived_output']
                outputs[q][k['configuration']]=r['archived_output']
    for r in ratings:assert r['configuration']==key[r['answer_id']]['configuration']
    departments=sorted({r['category'] for r in ratings});assert len(departments)==5
    human=[];wins=[];identity=[]
    for dept in departments:
        rows=[r for r in ratings if r['category']==dept]
        groups={r['group_id'] for r in rows};assert len(groups)==4
        for module,dimension,configs,expected in [('M1','fidelity','BC',24),('M2','relevance','ABC',36),('M2','faithfulness','ABC',36)]:
            for c in configs:
                selected=[r for r in rows if r['module']==module and r['dimension']==dimension and r['configuration']==c]
                values=[int(r['score']) for r in selected];assert len(values)==expected
                human.append(dict(department=dept,module=module,dimension=dimension,configuration=c,
                                  groups=4,queries=8 if module=='M1' else 12,ratings=len(values),
                                  score_sum=sum(values),mean=statistics.mean(values),median=statistics.median(values)))
        for dim in ['relevance','faithfulness']:
            totals=defaultdict(int)
            for r in rows:
                if r['module']=='M2' and r['dimension']==dim:totals[r['group_id'],r['language'],r['configuration']]+=int(r['score'])
            qs=sorted({(g,l) for g,l,c in totals})
            for a,b in [('B','A'),('C','A'),('B','C')]:
                differences=[totals[g,l,a]-totals[g,l,b] for g,l in qs]
                wins.append(dict(department=dept,dimension=dim,comparison=a+' minus '+b,
                                 queries=len(qs),first_higher=sum(x>0 for x in differences),
                                 second_higher=sum(x<0 for x in differences),tied=sum(x==0 for x in differences)))
        selected=[v for (g,l),v in outputs.items() if g in groups];assert len(selected)==12
        identity.append(dict(department=dept,queries=12,
                             A_B_identical=sum(v['A']==v['B'] for v in selected),
                             A_C_identical=sum(v['A']==v['C'] for v in selected),
                             B_C_identical=sum(v['B']==v['C'] for v in selected)))
    # Keep original pre-inference label coverage distinct from later reconciled labels.
    mappings=read(FINAL/'source_span_crosswalk.v1.json')['mappings']
    assert sha(FINAL/'source_span_crosswalk.v1.json')==read(FINAL/'execution_manifest.json')['source_crosswalk_sha256']
    archives={c:[json.loads(line) for line in (FINAL/c/'interactions.jsonl').read_text(encoding='utf-8').splitlines()] for c in 'ABC'}
    eligible={c:{r['question_id'] for r in rows if all(mappings[k].get('mapped_ids') for k in r['original_ground_truth_chunk_ids'])} for c,rows in archives.items()}
    assert all(len(v)==177 for v in eligible.values())
    metrics=list(csv.DictReader((FINAL/'per_query_metrics.csv').open(encoding='utf-8-sig')))
    by_config={c:{r['record_id']:r for r in metrics if r['configuration']==c} for c in 'ABC'}
    audit_groups={r['group_id'] for r in ratings};assert len(audit_groups)==20
    automatic=[]
    for population in ['full_test','human_audit_groups']:
        for metric in ['hit_at_k','mrr_at_k','faithfulness','context_precision','context_recall','answer_relevancy']:
            for version in (['original_177','reconciled_210'] if metric in ['hit_at_k','mrr_at_k'] else ['observed_judge_scores']):
                for dept in departments:
                    ids=[q for q,r in by_config['A'].items() if r['office']==dept
                         and (population=='full_test' or r['group_id'] in audit_groups)
                         and all(q in by_config[c] and by_config[c][q][metric] not in ('','None','nan') for c in 'ABC')
                         and (version!='original_177' or all(q in eligible[c] for c in 'ABC'))]
                    expected=42 if population=='full_test' else 12
                    row=dict(population=population,label_basis=version,department=dept,metric=metric,
                             planned_queries=expected,matched_queries=len(ids),missing_queries=expected-len(ids))
                    row.update({c:statistics.mean(float(by_config[c][q][metric]) for q in ids) if ids else None for c in 'ABC'})
                    automatic.append(row)
    OUT.mkdir(parents=True)
    table('human_scores_by_department.csv',human);table('automated_scores_by_department.csv',automatic)
    table('paired_query_counts.csv',wins);table('identical_answers.csv',identity)
    sources=[HUMAN/'analysis_results.json',HUMAN/'manifest.json',HUMAN/'analysis_plan.json',FINAL/'per_query_metrics.csv',FINAL/'source_span_crosswalk.v1.json',FINAL/'execution_manifest.json']
    report={'scope':'Post-hoc descriptive breakdown only; no department-level significance tests',
            'departments':5,'human_groups_per_department':4,'human_M2_queries_per_department':12,
            'human_M2_ratings_per_configuration_per_dimension_per_department':36,
            'human_M1_ratings_per_configuration_per_department':24,'model_calls':0,'score_edits':0,
            'source_hashes':{str(p.relative_to(ROOT)):sha(p) for p in sources},
            'note':'Raters are repeated measures. Counts are not independent participant or citizen counts. Automated means use shared observed cases in each cell.'}
    (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    for dept in departments:
        print('\n'+dept)
        for dim in ['relevance','faithfulness']:
            print('Human',dim,{r['configuration']:round(r['mean'],4) for r in human if r['department']==dept and r['dimension']==dim})
        for metric in ['hit_at_k','mrr_at_k','answer_relevancy','faithfulness']:
            r=next(r for r in automatic if r['department']==dept and r['population']=='full_test' and r['metric']==metric and r['label_basis']!='reconciled_210')
            print('Auto',metric,'n=',r['matched_queries'],{c:round(r[c],4) for c in 'ABC'})
        print('Identity',next(r for r in identity if r['department']==dept))


if __name__=='__main__':main()
