"""Three declared website-only smoke questions; no benchmark or judge calls."""
import hashlib
import argparse
import json
import time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = [
    ('taglish', 'ano need magpagawa ng building'),
    ('bislish', 'Unsa ang kinahanglan para magpatukod og building?'),
    ('english', 'What do I need to construct a building?'),
]


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--version',choices=['v1','v2'],required=True)
    args=parser.parse_args()
    OUT=ROOT/f'experiments/website-language-fidelity-{args.version}'
    OUT.mkdir(exist_ok=True)
    manifest = {'scope':'Website language smoke test, not thesis evaluation or factual certification.',
                'questions':QUESTIONS,'selection':'Declared before execution; first is reported user regression.',
                'prompt_sha256':hashlib.sha256((ROOT/f'config/website_response_language_{args.version}.json').read_bytes()).hexdigest(),
                'endpoint':'http://127.0.0.1:8001/api/query','judge_calls':0}
    target=OUT/'manifest.json'
    if target.exists():
        raise SystemExit('Preserve this run; use a new version for a rerun.')
    target.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    for language, question in QUESTIONS:
        print(f'Starting {language}: {question}',flush=True)
        started=time.monotonic()
        response=requests.post(manifest['endpoint'],json={'query':question,'response_language':'auto'},timeout=260)
        result={'question':question,'expected_language':language,'http_status':response.status_code,
                'seconds':round(time.monotonic()-started,2),'result':response.json()}
        (OUT/f'{language}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'language':language,'seconds':result['seconds'],'status':result['result'].get('status'),
                          'answer':result['result'].get('answer')},ensure_ascii=True),flush=True)


if __name__=='__main__':
    main()
