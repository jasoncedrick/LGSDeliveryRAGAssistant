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
from app.website import create_pipeline
from app.website_language import REQUESTED_LANGUAGE, PROMPT_SHA256


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
    cases=source['results']
    if args.ids:
        wanted=set(args.ids.split(','));cases=[r for r in cases if r['id'] in wanted]
        if len(cases)!=len(wanted):raise ValueError('Unknown case ID')
    manifest={'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
              'prompt_sha256':PROMPT_SHA256,
              'runtime_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'app/website_language.py',ROOT/'app/website_intake.py',ROOT/'app/website_normalizer.py',ROOT/'app/website.py',ROOT/'app/website_scope.py']},
              'case_ids':[r['id'] for r in cases], 'scope':'Post-study synthetic website regression; not thesis evaluation or validated accuracy scoring.'}
    if args.reuse:
        reuse=Path(args.reuse).resolve()
        previous=json.loads((reuse/'manifest.json').read_text())
        if any(previous[k]!=manifest[k] for k in ('archive_sha256','prompt_sha256','runtime_hashes')):
            raise ValueError('Cannot reuse results from a different candidate or input')
        manifest['reused_from']=str(reuse)
        if not (output/'results.jsonl').exists():
            records=[json.loads(line) for line in (reuse/'results.jsonl').read_text().splitlines()]
            expected={r['id']:r['query'] for r in cases}
            if any(expected.get(r['id'])!=r['query'] for r in records):raise ValueError('Reuse question mismatch')
            (output/'results.jsonl').write_bytes((reuse/'results.jsonl').read_bytes())
    mp=output/'manifest.json'
    if mp.exists() and json.loads(mp.read_text())!=manifest:
        raise ValueError('Candidate/input changed: preserve this run and use a new output folder')
    mp.write_text(json.dumps(manifest,indent=2))
    result_path=output/'results.jsonl'
    done={json.loads(line)['id'] for line in result_path.read_text().splitlines()} if result_path.exists() else set()
    def log(message):
        print(message,flush=True)
        with (output/'progress.log').open('a',encoding='utf-8') as f:f.write(message+'\n')
    log(f'Loading registered pipeline; {len(cases)} cases, {len(done)} archived')
    pipeline=create_pipeline()
    for n,case in enumerate(cases,1):
        if case['id'] in done:continue
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
    log('COMPLETE. Inspect raw answers and source support; statuses are not quality scores.')


if __name__=='__main__':main()
