"""Replay three archived RAGAS nulls offline; no LLM or embedding calls."""
from pathlib import Path
import hashlib
import json
import math
import importlib.metadata
ROOT=Path(__file__).resolve().parents[1]

def main():
    from ragas.llms.json_load import json_loader
    from ragas.metrics import context_precision,answer_relevancy
    source=ROOT/'experiments/t06-ragas-90query-development-v1'
    output=ROOT/'experiments/t06-ragas-null-diagnosis-v1'
    if output.exists():raise ValueError('Preserve existing diagnosis')
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    originals={p.name:digest(p) for p in source.iterdir() if p.is_file()}
    scores=json.loads((source/'scores.json').read_text(encoding='utf-8'))
    events=[json.loads(line) for line in (source/'judge_calls.jsonl').read_text(encoding='utf-8').splitlines()]
    targets={r['record_id']:r for r in scores if r['status']=='PARTIAL_OR_FAILED_JUDGE'}
    assert set(targets)=={'SCENARIO-CTO-003-english','SCENARIO-OCBO-006-english','SCENARIO-BFP-004-taglish'}
    class NoModel:
        def generate_text(self,*args,**kwargs):raise AssertionError('Model calls prohibited during replay')
    findings=[];traces=[]
    for rid,record in targets.items():
        metric=next(k for k,v in record['scores'].items() if v is None)
        active=None;outputs=[];case_events=[]
        for line,event in enumerate(events,1):
            if event.get('record_id')!=rid:continue
            case_events.append({'trace_line_1_based':line,**event})
            if event['event']=='judge_prompt':
                prompt=event['prompts'][0]
                active=('context_precision' if prompt.startswith('Given question, answer and context verify') else
                        'answer_relevancy' if prompt.startswith('Generate a question for the given answer') else 'other')
            elif event['event']=='judge_output' and active==metric:
                for group in event['outputs']:
                    for text in group:outputs.append({'trace_line_1_based':line,'raw_output':text})
        parsed=[json_loader._safe_load(x['raw_output'],NoModel()) for x in outputs]
        if metric=='context_precision':
            assert len(parsed)==5
            replay=context_precision._calculate_average_precision(parsed)
            assert isinstance(parsed[-1],dict) and 'verification' in parsed[-1] and 'verdict' not in parsed[-1]
            cause='Fifth context verdict is nested under verification; RAGAS looks only for a top-level verdict. The missing value propagates NaN through average precision.'
            expected='One JSON object per context, with top-level reason and verdict; verdict must be string "0" or "1" for this installed implementation.'
        else:
            assert len(parsed)==3
            replay=answer_relevancy._calculate_score(parsed,{'question':'offline format replay'})
            if 'OCBO' in rid:
                assert all(isinstance(x,dict) and 'answer' in x and 'question' not in x for x in parsed)
                cause='All three outputs use answer and context fields instead of the required top-level question. RAGAS sees only empty generated questions and returns NaN before embedding.'
            else:
                assert all(isinstance(x,list) and len(x)==8 for x in parsed)
                cause='Each of the three outputs contains eight consecutive JSON objects. The RAGAS loader returns a list for each output; answer relevancy ignores non-dict entries, obtains no questions and returns NaN before embedding.'
            expected='Exactly one JSON object per generation, with top-level question (string) and noncommittal (integer 0 or 1). No repeated objects or arrays.'
        assert math.isnan(float(replay))
        findings.append({'record_id':rid,'metric':metric,'cause':cause,'expected_contract':expected,
                         'replayed_original_null':True,'output_count':len(outputs),
                         'parsed_types':[type(x).__name__ for x in parsed],
                         'evidence':[dict(o,parsed=p) for o,p in zip(outputs,parsed)],
                         'transport_error_events':sum(x['event']=='judge_error' for x in case_events)})
        traces.extend(case_events)
    assert all(digest(source/name)==h for name,h in originals.items())
    output.mkdir()
    write=lambda name,v:(output/name).write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    import inspect
    modules=[Path(inspect.getfile(type(context_precision))),Path(inspect.getfile(type(answer_relevancy))),Path(inspect.getfile(type(json_loader)))]
    write('findings.json',{'status':'THREE_NULLS_REPRODUCED_OFFLINE','ragas_version':importlib.metadata.version('ragas'),
        'findings':findings,'model_calls':0,'embedding_calls':0,'original_scores_modified':False,
        'library_source_hashes':{str(p):digest(p) for p in modules},'input_hashes':originals,
        'limits':['Trace callbacks did not save run IDs; matching uses record IDs and homogeneous metric prompt/output blocks, checked against expected output counts.',
                  'These failures establish evaluator output-contract violations, not answer correctness or retrieval correctness.',
                  'No timeout cause is needed to reproduce these nulls; no judge_error events were logged for these cases.'],
        'next_action':'Version an evaluator-only strict-output instruction for both metrics; test on this three-case diagnostic subset. Preserve originals, and never mix subset retries into the full-run mean without a documented comparison protocol.'})
    write('selected_traces.json',traces)
    lines=['STEP 1 - OFFLINE RAGAS NULL DIAGNOSIS','',
           'All three nulls were reproduced from saved judge outputs using the installed RAGAS parser and metric functions. No server, model generation, embeddings, or source-answer edits were used. Original files remain hash-identical.','']
    for x in findings:lines += [x['record_id']+' / '+x['metric'],x['cause'],'Expected: '+x['expected_contract'],'']
    lines += ['Interpretation: the evaluator did not receive the JSON shape its scoring code requires. This does not establish that the citizen-facing answer is correct. Do not rename fields, unwrap objects or select a convenient question retroactively to replace the published nulls.',
              '', 'Recommended next small step: add versioned evaluator-only output constraints and local contract tests, then run only these three cases in a new diagnostic folder when the local model server is available. A three-case retry is a diagnostic result, not an unbiased replacement full-set score.',
              '', 'Manual action: none needed to establish these causes. Model server required only for a new judge run. Source/reference validation (step 2) remains separate and has not started in this diagnosis.']
    (output/'READ_THIS_FIRST.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    write('hashes.json',{p.name:digest(p) for p in output.iterdir() if p.is_file()})
    print('PASS: 3 original nulls reproduced; zero model/embedding calls; original hashes unchanged.')

if __name__=='__main__':main()
