"""Apply the reviewed keep list only in the isolated release worktree."""
import ast
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
assert ROOT == Path('D:/thesis/LGSDeliveryRAGAssistant-release-20261112')
assert subprocess.check_output(['git','branch','--show-current'],cwd=ROOT).decode().strip() == 'release/clean-adviser-20261112'
keep = json.loads((ROOT/'docs/cleanup/core_keep_list.json').read_text())
tracked = subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
registration = json.loads((ROOT/'experiments/t07-final-evaluation-v1/candidate_registration.json').read_text())
protected = {p.replace('\\','/') for p in registration['file_hashes']}
scripts = set(keep['scripts']) | {p.name for p in (ROOT/'scripts').glob('*website*')}
scripts |= {'build_citizen_vercel.cjs','stop_citizen_public_demo.ps1','check_adviser_demo.py',
            'run_final_human_rate_audit.py','compute_m4_automated_stats.py','generate_all_m4_figures.py',
            'clean_release_tree.py'}
tests = set(keep['tests']) | {'test_citizen_website.py','test_website_language.py','test_website_queue.py','test_website_qa_contract.py','__init__.py'}
# Retain local script imports needed by the preserved tests and pipeline scripts.
changed = True
while changed:
    before = set(scripts)
    for p in [ROOT/'scripts'/n for n in scripts] + [ROOT/'tests'/n for n in tests]:
        if p.suffix != '.py' or not p.exists(): continue
        for node in ast.walk(ast.parse(p.read_text(encoding='utf-8-sig'))):
            modules = [a.name for a in node.names] if isinstance(node,ast.Import) else ([node.module or ''] + [a.name for a in node.names] if isinstance(node,ast.ImportFrom) else [])
            for module in modules:
                name = module.split('.')[-1] + '.py'
                if (ROOT/'scripts'/name).exists(): scripts.add(name)
    changed = before != scripts
removed = []
for relative in filter(None,tracked):
    p = Path(relative); parts=p.parts
    delete = False
    if parts[0] == 'experiments': delete = len(parts)<3 or parts[1] not in keep['experiments']
    elif parts[0] in {'output','outputs','scrape','text_extraction steps','audit_ui'}: delete=True
    elif parts[0] == 'scripts': delete=p.name not in scripts
    elif parts[0] == 'tests': delete=p.name not in tests
    elif parts[0] == 'data': delete=len(parts)==2 and p.name in {'eboss_corpus_chunks_v1.json','bm25_index.pkl','faiss_index.bin','Master_Candidate_Terms.xlsx','compiledictionary.py'}
    elif len(parts)==1: delete=p.suffix.lower() in {'.pdf','.png'} or p.name in {'new t06-t07.md','t03.md','t05_completion.md','t06-t07.md','We-have-built-the-research-prototyp.md'}
    if delete and relative not in protected:
        target=(ROOT/p).resolve()
        assert target.is_relative_to(ROOT)
        removed.append({'path':relative,'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()})
(ROOT/'docs/cleanup/removed_files.json').write_text(json.dumps({'archive_tag':'archive/pre-clean-demo-20261112','files':removed},indent=2),encoding='utf-8')
for offset in range(0,len(removed),40):
    subprocess.run(['git','rm','--']+[r['path'] for r in removed[offset:offset+40]],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
print('Archived from active tree:',len(removed),'files;',round(sum(r['bytes'] for r in removed)/1024**2,1),'MiB. All recoverable through archive tag.')
