"""Strict offline input/resume checks for the exploratory website regression."""
import json
import re
from pathlib import Path


def validate_cases(cases, expected_count=200):
    if not isinstance(cases, list) or len(cases) != expected_count:
        raise ValueError(f'Expected {expected_count} exploratory cases')
    seen_ids, seen_queries = set(), set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError('Case must be an object')
        cid, query = case.get('id'), case.get('query')
        if not isinstance(cid, str) or not re.fullmatch(r'Q\d{3}', cid):
            raise ValueError('Invalid case ID')
        if not isinstance(query, str) or not query.strip():
            raise ValueError(f'Empty query: {cid}')
        if cid in seen_ids or query.strip() in seen_queries:
            raise ValueError(f'Duplicate case ID or query: {cid}')
        if not isinstance(case.get('category'), str) or not isinstance(case.get('data'), dict):
            raise ValueError(f'Missing category/baseline: {cid}')
        seen_ids.add(cid)
        seen_queries.add(query.strip())
    return cases


def select_cases(cases, requested):
    if not requested:
        return cases
    ids = [cid.strip() for cid in requested.split(',')]
    if not all(ids) or len(ids) != len(set(ids)):
        raise ValueError('Requested IDs must be nonempty and unique')
    wanted = set(ids)
    selected = [c for c in cases if c['id'] in wanted]
    if len(selected) != len(wanted):
        raise ValueError('Unknown case ID')
    return selected


def validate_records(records, cases, require_complete=False):
    expected = {c['id']: c for c in cases}
    seen = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError('Archived record must be an object')
        cid = record.get('id')
        if cid not in expected or cid in seen:
            raise ValueError(f'Unknown or duplicate archived ID: {cid}')
        case = expected[cid]
        for field, case_field in [('query', 'query'), ('category', 'category'), ('baseline', 'data')]:
            if record.get(field) != case[case_field]:
                raise ValueError(f'Archived {field} differs from input: {cid}')
        result = record.get('candidate')
        if not isinstance(result, dict) or not isinstance(result.get('status'), str) or not result['status']:
            raise ValueError(f'Missing candidate status: {cid}')
        seen.add(cid)
    if require_complete and seen != set(expected):
        raise ValueError('Regression is incomplete; do not report a complete run')
    return seen


def read_records(path):
    path = Path(path)
    if not path.exists():
        return []
    raw = path.read_bytes()
    # A truncated last append needs inspection, never automatic removal/retry.
    if raw and not raw.endswith(b'\n'):
        raise ValueError('Incomplete JSONL append; preserve the file and inspect before resuming')
    records = []
    for number, line in enumerate(raw.decode('utf-8').splitlines(), 1):
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f'Invalid JSONL record at line {number}; original retained') from exc
    return records


def completion(records, cases):
    validate_records(records, cases, require_complete=True)
    exceptions = [r['id'] for r in records if r['candidate']['status'] == 'QA_EXCEPTION']
    return {'execution': 'COMPLETE_WITH_ERRORS' if exceptions else 'COMPLETE',
            'records': len(records), 'exception_ids': exceptions,
            'answer_quality': 'NOT_CERTIFIED', 'promotion': 'NOT_AUTHORIZED_BY_EXECUTION'}
