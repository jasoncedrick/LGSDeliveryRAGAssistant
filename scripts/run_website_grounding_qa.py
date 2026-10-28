"""Visible, resumable post-study regression. Never reads a held-out benchmark.

Run from the repository root. Output belongs under ignored tmp/, not public Git.
Each completed record is appended once. No automated judge or output repair.
"""
import argparse
import hashlib
import json
import sys
import time
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.website import create_pipeline, registered_profile, Runtime
from app.website_language import REQUESTED_LANGUAGE, PROMPT_SHA256, PROMPT_PATH
from scripts.website_qa_contract import validate_cases, select_cases, read_records, validate_records, completion


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--archive',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--ids',default='')
    parser.add_argument('--reuse',default='')
    args=parser.parse_args()
    output=Path(args.output).resolve()
    if not output.is_relative_to((ROOT/'tmp').resolve()):
        raise ValueError('Raw diagnostic output must stay under ignored project tmp/')
    output.mkdir(parents=True,exist_ok=True)
    archive=Path(args.archive)
    with zipfile.ZipFile(archive) as z:
        source=json.loads(z.read('eboss-200-repeat-20261028/results.json'))
    cases=select_cases(validate_cases(source['results']),args.ids)
    candidate, registered_hashes=registered_profile()
    manifest={'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
              'prompt_sha256':PROMPT_SHA256,
              'prompt_path':str(PROMPT_PATH.relative_to(ROOT)),
              'registered_hashes':registered_hashes, 'model_digest':candidate['model_digest'],
              'runtime_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'app/website_language.py',ROOT/'app/website_intake.py',ROOT/'app/website_normalizer.py',ROOT/'app/website.py',ROOT/'app/website_scope.py',Path(__file__).resolve(),ROOT/'scripts/website_qa_contract.py']},
              'case_ids':[r['id'] for r in cases], 'scope':'Post-study synthetic website regression; not thesis evaluation or validated accuracy scoring.'}
    if args.reuse:
        reuse=Path(args.reuse).resolve()
        previous=json.loads((reuse/'manifest.json').read_text())
        if any(previous.get(k)!=manifest[k] for k in ('archive_sha256','prompt_sha256','runtime_hashes','registered_hashes','model_digest')):
            raise ValueError('Cannot reuse results from a different candidate or input')
        manifest['reused_from']=str(reuse)
        reused=read_records(reuse/'results.jsonl')
        validate_records(reused,cases)
    mp=output/'manifest.json'
    if mp.exists() and json.loads(mp.read_text())!=manifest:
        raise ValueError('Candidate/input changed: preserve this run and use a new output folder')
    # Check destination BEFORE copying anything from a reusable focused run.
    if args.reuse and not (output/'results.jsonl').exists():
        (output/'results.jsonl').write_bytes((reuse/'results.jsonl').read_bytes())
    mp.write_text(json.dumps(manifest,indent=2))
    result_path=output/'results.jsonl'
    records=read_records(result_path)
    done=validate_records(records,cases)
    def log(message):
        print(message,flush=True)
        with (output/'progress.log').open('a',encoding='utf-8') as f:f.write(message+'\n')
    if len(done)==len(cases):
        report=completion(records,cases)
        (output/'execution.json').write_text(json.dumps(report,indent=2)+'\n')
        log(f"{report['execution']}: existing records verified; no model loaded or called.")
        return 1 if report['exception_ids'] else 0
    log(f'Loading registered pipeline; {len(cases)} cases, {len(done)} archived')
    pipeline=create_pipeline()
    runtime=Runtime();runtime.pipeline=pipeline
    if runtime.model_state()!='ready':
        raise RuntimeError('Registered model unavailable or digest differs; no cases generated')
    for n,case in enumerate(cases,1):
        if case['id'] in done:continue
        if runtime.model_state()!='ready':
            raise RuntimeError('Model became unavailable or changed; completed records retained')
        log(f"[{n}/{len(cases)}] {case['id']} START")
        pipeline.normalizer.last_trace=None
        start=time.monotonic();token=REQUESTED_LANGUAGE.set('auto')
        try:
            result=pipeline.handle_query(case['query'])
        except Exception as e:
            result={'status':'QA_EXCEPTION','error':str(e)}
        finally:REQUESTED_LANGUAGE.reset(token)
        record={'id':case['id'],'query':case['query'],'category':case['category'],
                'baseline':case['data'],'candidate':result,
                'normalization_trace':pipeline.normalizer.last_trace,
                'elapsed_seconds':round(time.monotonic()-start,3)}
        with result_path.open('a',encoding='utf-8') as f:f.write(json.dumps(record,ensure_ascii=True)+'\n')
        log(f"[{n}/{len(cases)}] {case['id']} {result['status']} {record['elapsed_seconds']}s")
    report=completion(read_records(result_path),cases)
    # Detect file changes during a long run before declaring a coherent candidate.
    for relative, expected in manifest['runtime_hashes'].items():
        if hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()!=expected:
            raise ValueError('Runtime changed during QA; preserve this mixed run: '+relative)
    if hashlib.sha256(PROMPT_PATH.read_bytes()).hexdigest()!=manifest['prompt_sha256']:
        raise ValueError('Prompt changed during QA; preserve this mixed run')
    if registered_profile()[1]!=manifest['registered_hashes']:
        raise ValueError('Registered artifacts changed during QA; preserve this run')
    if hashlib.sha256(archive.read_bytes()).hexdigest()!=manifest['archive_sha256']:
        raise ValueError('Question archive changed during QA; preserve this run')
    (output/'execution.json').write_text(json.dumps(report,indent=2)+'\n')
    log(report['execution']+'. Execution completion is not answer-quality approval.')
    return 1 if report['exception_ids'] else 0


if __name__=='__main__':sys.exit(main())
