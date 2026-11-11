"""Read-only demo preflight. Does not generate answers or change research files."""
import argparse
import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.website import registered_profile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8000)
    args = parser.parse_args()
    try:
        candidate, checked = registered_profile()
        print(f'PASS: {len(checked)} registered runtime files and five source PDFs verified.')
        models = requests.get('http://127.0.0.1:11434/api/tags', timeout=10)
        models.raise_for_status()
        model = next((m for m in models.json()['models'] if m['name'] in
                      (candidate['model'], candidate['model'] + ':latest')), None)
        if model is None or model['digest'] != candidate['model_digest']:
            raise ValueError('Registered eboss-mistral model is missing or has a different digest.')
        print('PASS: Ollama and registered model are available.')
        print('Profile: Config B, K=3, BM25=.75 / dense=.25 / dictionary retrieval boost=0.')
        print('Website language adapter: v2, separate from frozen study generation.')
    except (requests.RequestException, ValueError, KeyError, OSError) as exc:
        print(f'FAIL: {exc}\nOpen Ollama if stopped; do not substitute a different model.')
        return 1
    try:
        health = requests.get(f'http://127.0.0.1:{args.port}/health', timeout=5)
        health.raise_for_status()
        print('Existing web server health:', json.dumps(health.json()))
        print('An existing server response alone does not prove which checkout owns its process.')
    except (requests.RequestException, ValueError):
        print('No responding website on the selected port. START_DEMO.ps1 can start it.')
    print('Preflight verifies runtime availability, not answer correctness. See demo/DEMO_GUIDE.md.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
