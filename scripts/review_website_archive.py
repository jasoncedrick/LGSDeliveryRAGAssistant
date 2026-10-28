"""Inspect saved exploratory answers without inference or rewriting dispositions.

Flags are diagnostics, not factual accuracy labels. Replay only the current
coverage predicate on the originally retrieved passages, never new generation.
"""
import argparse
import collections
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.website_scope import coverage_issue
from scripts.website_qa_contract import read_records


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',default='tmp/grounding-v4-full')
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    source=(ROOT/args.input).resolve();output=(ROOT/args.output).resolve()
    if output.exists() or not output.is_relative_to((ROOT/'tmp').resolve()):
        raise ValueError('Use a new report file beneath ignored tmp/')
    original=json.loads((ROOT/'outputs/website-grounding-qa-20261028/summary.json').read_text())
    if sha(source/'results.jsonl')!=original['results_sha256']:
        raise ValueError('This is not the preserved 200-case archive')
    rows=read_records(source/'results.jsonl')
    expected=original['input_and_runtime_manifest']['case_ids']
    ids=[r['id'] for r in rows]
    if len(set(ids))!=200 or sorted(ids)!=sorted(expected):
        raise ValueError('Missing or duplicate archived case')
    details=[]
    for row in sorted(rows,key=lambda r:r['id']):
        result=row['candidate'];answer=result.get('answer') or '';diag=result.get('diagnostics',{})
        citations=result.get('citations',[]);allowed={c['citation'] for c in citations}
        flags=[]
        mentioned=set(re.findall(r'\bS\d+\b',answer))
        if mentioned-allowed:flags.append('unknown_citation_label')
        if result.get('status')=='ANSWERED' and not re.search(r'\[S\d+(?:,\s*S\d+)*\]',answer):
            flags.append('no_valid_bracketed_citation')
        if re.search(r'\b(?:DEV120|CHUNK)-',answer):flags.append('internal_chunk_identifier')
        if result.get('status')=='ANSWERED' and answer.startswith('Wala akoy nakit-an nga impormasyon'):
            flags.append('fallback_like_text_marked_answered')
        clues=set(re.findall(r'[a-z]+',answer.lower())) & {'kung','iyong','kayo','muna','magbayad','akong','dili','kinahanglan'}
        if diag.get('response_language')=='english' and len(clues)>=2:
            flags.append('possible_wrong_language')
        old=diag.get('coverage_issue')
        new=coverage_issue(row['query'],citations) if citations else old
        details.append({'id':row['id'],'archived_status':result['status'], 'diagnostic_flags':flags,
                        'archived_coverage_issue':old,'replayed_coverage_issue':new,
                        'coverage_changed':old!=new})
    report={'scope':'Saved exploratory traces only; not new responses or factual accuracy scores',
            'records':len(rows),'source_results_sha256':sha(source/'results.jsonl'),
            'current_scope_sha256':sha(ROOT/'app/website_scope.py'),
            'review_script_sha256':sha(Path(__file__).resolve()),
            'model_calls':0,'original_records_changed':False,
            'flag_counts':dict(collections.Counter(f for row in details for f in row['diagnostic_flags'])),
            'changed_coverage_ids':[r['id'] for r in details if r['coverage_changed']],
            'known_unresolved_counterexamples':['Q001','Q003','Q004','Q006','Q088','Q134','Q135','Q136'],
            'answer_quality_gate':'NOT_PASSED',
            'limitations':['A clean citation format does not establish source support.',
                           'Language clues and refusal prefixes are screening flags, not validated classifiers.',
                           'The topic-loop correction addresses a synthetic regression; replay cannot establish new answer quality.',
                           'Earlier source-entailment findings remain unresolved; no fresh answers generated.'],
            'cases':details}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='cases'},indent=2))


if __name__=='__main__':main()
