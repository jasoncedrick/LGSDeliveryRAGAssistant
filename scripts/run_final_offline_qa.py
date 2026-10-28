"""Fresh, visible QA without model calls, deployment or rewriting research results.

Run with the project venv. Each run uses a NEW ignored output directory. Browser
checks use a temporary loopback-only server with model initialization disabled.
This is a software/archive gate, never factual accuracy or promotion approval.
"""
import argparse
import csv
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify_paper():
    package=ROOT/'outputs/team-handoff-20261029'
    human=ROOT/'experiments/t10-t12-human-analysis-v1'
    checked={}
    for folder, manifest in [(package,read(package/'PACKAGE_MANIFEST.json')),
                             (ROOT/'outputs/manuscript-closeout-20261028',read(ROOT/'outputs/manuscript-closeout-20261028/PACKAGE_MANIFEST.json')),
                             (human,read(human/'manifest.json'))]:
        for name, entry in manifest['files'].items():
            expected=entry['sha256'] if isinstance(entry,dict) else entry
            p=folder/name
            require(sha(p)==expected,'Archive file changed: '+str(p.relative_to(ROOT)))
            checked[str(p.relative_to(ROOT))]=expected
    sources=read(package/'source_manifest.json')
    for name,expected in sources['files'].items():
        require(sha(ROOT/name)==expected,'Paper source changed: '+name)
    require(sha(Path('D:/thesis/20260923.pdf'))==sources['manuscript_sha256'],'Manuscript version differs')
    require(sha(Path('C:/Users/User/Downloads/thesis_progress_tracker.xlsx'))==sources['original_tracker_sha256'],'Authoritative tracker version differs')
    # Check the numerical tables against the original per-query metric archive.
    final=ROOT/'experiments/t07-final-evaluation-v1'
    metrics=list(csv.DictReader((final/'per_query_metrics.csv').open(encoding='utf-8-sig')))
    maps={c:{r['record_id']:r for r in metrics if r['configuration']==c} for c in 'ABC'}
    for row in csv.DictReader((final/'matched_metrics.csv').open(encoding='utf-8-sig')):
        metric=row['metric']
        good=[q for q in maps['A'] if all(maps[c][q][metric] not in ('','None','nan') for c in 'ABC')]
        require(len(good)==int(row['matched_queries']),'Wrong matched denominator')
        for c in 'ABC':
            require(abs(sum(float(maps[c][q][metric]) for q in good)/len(good)-float(row[c]))<1e-12,'Matched mean differs')
    mappings=read(final/'source_span_crosswalk.v1.json')['mappings']
    require(sha(final/'source_span_crosswalk.v1.json')==read(final/'execution_manifest.json')['source_crosswalk_sha256'],'Original label version differs')
    primary=list(csv.DictReader((package/'tables/automated_original_label_subset.csv').open(encoding='utf-8-sig')))
    for c in 'ABC':
        records=[json.loads(line) for line in (final/c/'interactions.jsonl').read_text(encoding='utf-8').splitlines()]
        eligible={r['question_id'] for r in records if all(mappings[k].get('mapped_ids') for k in r['original_ground_truth_chunk_ids'])}
        require(len(eligible)==177,'Original retrieval subset differs')
        for metric in ['hit_at_k','mrr_at_k']:
            row=next(r for r in primary if r['metric']==metric)
            value=sum(float(maps[c][q][metric]) for q in eligible)/len(eligible)
            require(abs(value-float(row[c]))<1e-12,'Original retrieval mean differs')
    result=read(human/'analysis_results.json')
    for name in ['descriptive_scores.csv','reliability.csv','paired_comparisons.csv','no_claim_sensitivity.csv']:
        require(sha(human/name)==sha(package/'tables'/name),'Human table changed: '+name)
    for row in csv.DictReader((package/'tables/human_score_distributions.csv').open(encoding='utf-8-sig')):
        entry=next(r for r in result['descriptives'] if all(str(r[k])==row[k] for k in ['module','dimension','configuration','language']))
        for i in range(1,6):
            require(int(row[f'score_{i}'])==entry[f'score_{i}'],'Frequency differs')
    for doc in [ROOT/'TEAM_START_HERE.md',*package.glob('*.md')]:
        for link in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf-8')):
            if not link.startswith(('https://','http://','#')):
                require((doc.parent/link.split('#')[0]).exists(),'Broken document link: '+link)
    return {'passed':True,'verified_archive_files':len(checked),'archive_hashes':checked,
            'matched_automated_means':'RECOMPUTED_MATCH','original_177_query_retrieval':'RECOMPUTED_MATCH',
            'human_tables_and_frequencies':'MATCH','chapter_package':'UNCHANGED',
            'visual_pdf_review':'Not repeated: identical PDF to the visually reviewed handoff',
            'private_collection_independence':'Researcher-confirmed; not inferred by this QA'}


def source_snapshot():
    paths=set()
    for pattern in ['app/website*.py','tests/test_*website*.py','tests/test_citizen_website.py',
                    'tests/test_human_audit_statistics.py','tests/test_triple_audit.py',
                    'scripts/*website*.py','scripts/*website*.cjs','scripts/run_final_offline_qa.py',
                    'scripts/build_citizen_vercel.cjs',
                    'website/*.js','website/*.html','website/*.css','config/website*.json']:
        paths.update(ROOT.glob(pattern))
    return {str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default='tmp/final-offline-qa-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
    parser.add_argument('--serve-only',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--port',type=int,default=0,help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.serve_only:
        import uvicorn
        from app.website import create_app
        uvicorn.run(create_app(start_runtime=False),host='127.0.0.1',port=args.port,log_level='warning')
        return 0
    output=(ROOT/args.output).resolve()
    require(output.is_relative_to((ROOT/'tmp').resolve()) and not output.exists(),'Use a NEW directory under ignored tmp/')
    output.mkdir(parents=True)
    report={'started_utc':datetime.now(timezone.utc).isoformat(),'model_calls':0,'deployed':False,
            'steps':[], 'source_hashes':source_snapshot(), 'answer_quality_gate':'NOT_PASSED',
            'limitation':'Software/archive checks do not validate generated claims or collection independence.'}
    server=None
    def run(name,command,env=None):
        print(f'[{len(report["steps"])+1}] {name} ...',flush=True)
        log=output/(name+'.log')
        with log.open('w',encoding='utf-8') as f:
            result=subprocess.run(command,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=240)
        step={'name':name,'exit_code':result.returncode,'log_sha256':sha(log)}
        text=log.read_text(encoding='utf-8')
        match=re.search(r'Ran (\d+) tests?',text)
        if match:step['tests']=int(match.group(1))
        report['steps'].append(step)
        require(result.returncode==0,f'{name} failed; inspect {log}')
        print('    PASS'+(f' ({step["tests"]} tests)' if match else ''),flush=True)
    try:
        print('Checking frozen profile, original archives and paper tables ...',flush=True)
        from app.website import registered_profile
        candidate,hashes=registered_profile()
        report['frozen_profile']={'k':candidate['k'],'weights':candidate['weights_B_C'],'hashes':hashes}
        report['paper']=verify_paper()
        env={**os.environ,'PYTHONIOENCODING':'utf-8','PYTHONUTF8':'1'}
        run('website-unit',[sys.executable,'-m','unittest','tests.test_citizen_website','tests.test_website_language','tests.test_website_queue','tests.test_website_grounding','tests.test_website_qa_contract','-v'],env)
        # Separate processes avoid mixing inference and statistics library state.
        run('human-statistics',[sys.executable,'-m','unittest','tests.test_human_audit_statistics','-v'],env)
        run('triple-audit',[sys.executable,'-m','unittest','tests.test_triple_audit','-v'],env)
        with socket.socket() as s:
            s.bind(('127.0.0.1',0));port=s.getsockname()[1]
        with (output/'server.log').open('w',encoding='utf-8') as log:
            server=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--serve-only','--port',str(port)],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,
                                    creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        base=f'http://127.0.0.1:{port}'
        deadline=time.monotonic()+30
        while True:
            try:
                with urllib.request.urlopen(base+'/api/sources',timeout=1) as response:
                    require(len(json.load(response))==5,'Expected five source documents')
                break
            except (OSError,TimeoutError):
                require(server.poll() is None and time.monotonic()<deadline,'Isolated QA server failed to start')
                time.sleep(.2)
        env.update(WEBSITE_TEST_URL=base,WEBSITE_QA_OUTPUT=str(output/'browser'),WEBSITE_MOTION_QA_OUTPUT=str(output/'motion'))
        run('browser',['node','scripts/test_citizen_website_browser.cjs'],env)
        run('motion',['node','scripts/test_website_motion.cjs'],env)
        report['browser']=read(output/'browser/browser-qa.json')
        report['motion']=read(output/'motion/qa.json')
        require(report['browser']['passed'] and report['motion']['passed'],'Browser receipt failed')
        env.update(WEBSITE_BUILD_QA_OUTPUT=str(output/'static-build'),PUBLIC_RAG_API_ORIGIN='https://qa.invalid')
        run('static-build',['node','scripts/build_citizen_vercel.cjs'],env)
        build=output/'static-build'
        files=[p for p in build.rglob('*') if p.is_file()]
        require(len(list((build/'static/sources').glob('*.pdf')))==5,'Static build lacks five PDFs')
        require(not any(part in {'private','received-ratings','experiments','outputs','.env'} for p in files for part in p.relative_to(build).parts),'Unexpected private/research build path')
        report['static_build']={'passed':True,'files':len(files),'source_pdfs':5,'qa_only_origin':'https://qa.invalid','production_build_untouched':True}
        require(source_snapshot()==report['source_hashes'],'Source changed during checks; preserve this run and start a new one')
        # Verify all sealed research files a second time to detect accidental mutation.
        require(verify_paper()==report['paper'],'Paper/archive changed during checks')
        require(registered_profile()[1]==hashes,'Frozen profile changed during checks')
        report['software_and_archive_qa']='PASS'
    except Exception as exc:
        report['software_and_archive_qa']='FAIL'
        report['failure']=str(exc)
        print('FAIL: '+str(exc),flush=True)
    finally:
        if server is not None:
            server.terminate()
            try:server.wait(timeout=10)
            except subprocess.TimeoutExpired:server.kill();server.wait(timeout=10)
        report['finished_utc']=datetime.now(timezone.utc).isoformat()
        (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f'Report: {output / "report.json"}',flush=True)
    print('No model calls or deployment. Factual answer quality remains a separate gate.',flush=True)
    return 0 if report['software_and_archive_qa']=='PASS' else 1


if __name__=='__main__':sys.exit(main())
