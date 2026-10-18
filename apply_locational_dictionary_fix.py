"""Change only DICT-OCBO-055, preserve other file text, back up and log."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import os

TERM='locational clearance'
CHANGES={
    'verified_english_definition':'Locational Clearance (LC), a written authority or permit granted by the City Planning and Development Office (CPDO) pursuant to applicable land-use planning and zoning laws for the establishment or operation of projects of national or local significance.',
    'governance_context_tag':'CPDO',
    'polysemy_flag':False,
    'disambiguation_rule':'',
    'curation_source':'manual; Davao City Citizens Charter 2026, CPDO, printed pages 640, 648, 655, 695 and 699 (PDF pages 11, 19, 26, 66 and 70); OCBO, printed pages 491 and 567 (PDF pages 3 and 79)'
}
def digest(data):return hashlib.sha256(data).hexdigest()
def apply(root):
    root=Path(root).resolve();path=root/'data/municipal_dictionary_v1.json'
    original=path.read_bytes();bom=original.startswith(b'\xef\xbb\xbf');text=original.decode('utf-8-sig')
    dictionary=json.loads(text);old=dictionary[TERM]
    if old.get('term_id')!='DICT-OCBO-055':raise ValueError('Unexpected term ID. No file modified.')
    if all(old.get(k)==v for k,v in CHANGES.items()):
        print('Already applied: DICT-OCBO-055. No changes made.');return
    if old.get('verified_english_definition')!='Certificate of Locational Viability' or old.get('polysemy_flag') is not True:
        raise ValueError('This entry differs from the reviewed original. No file modified; send the current entry.')
    matches=list(re.finditer(r'(?m)^([ \t]*)"locational clearance"\s*:\s*',text))
    if len(matches)!=1:raise ValueError('Cannot identify a unique entry span. No file modified.')
    m=matches[0];start=m.end();value,end=json.JSONDecoder().raw_decode(text,start)
    if value!=old:raise ValueError('Entry span mismatch. No file modified.')
    new=dict(old);new.update(CHANGES)
    newline='\r\n' if '\r\n' in text else '\n'
    rendered=json.dumps(new,ensure_ascii=False,indent=2).replace('\n',newline+m.group(1))
    updated=text[:start]+rendered+text[end:]
    after=json.loads(updated)
    changed=[k for k in dictionary if dictionary[k]!=after[k]]
    if set(dictionary)!=set(after) or changed!=[TERM]:raise ValueError('Unexpected changes. No file modified.')
    data=(b'\xef\xbb\xbf' if bom else b'')+updated.encode('utf-8')
    stamp=datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backup=root/'backups'/('locational-dictionary-'+stamp)
    logdir=root/'experiments/dictionary-changes'/('locational-'+stamp)
    backup.mkdir(parents=True,exist_ok=False);logdir.mkdir(parents=True,exist_ok=False)
    backupfile=backup/path.name;shutil.copy2(path,backupfile)
    record={'status':'PREPARED','created_utc':datetime.now(timezone.utc).isoformat(),
        'target':str(path),'backup':str(backupfile),'entry':TERM,'term_id':'DICT-OCBO-055',
        'before_file_sha256':digest(original),'after_file_sha256':digest(data),
        'changes':{k:{'before':old.get(k),'after':v} for k,v in CHANGES.items()},
        'reason':'The supplied CPDO services share one core locational-clearance definition. Building/business applications are procedural variants; the old options omit two-storey construction and appeals and interrupt nine already contextualized development queries. No general contextual resolver or scenario-based routing is added.',
        'source':{'City Planning CGD_Citizen Charter 2026_VOL.I & II-3.pdf':{'sha256':'6d1572dc7ef1122064b3db8d799f27356231dd2cbeafb84231c6f315820b1005','printed_pages':[640,648,655,695,699],'pdf_relative_pages':[11,19,26,66,70]},'OCBD Pages from CGD_Citizen Charter 2026_VOL.I & II-2.pdf':{'sha256':'6f081dde0a63ade8aaa3f4dc5a26ceb0c7fde85f896951931d8222eaa86b3093','printed_pages':[491,567],'pdf_relative_pages':[3,79]}},
        'review_basis':'User-supplied PDFs, rendered-page review, and the nine DICT-OCBO-055 stops in the existing development query log; no independent domain-review approval asserted.',
        'other_dictionary_entries_changed':False,'corpus_changed':False,'indexes_rebuilt':False,'benchmarks_changed':False}
    log=logdir/'change_log.json';log.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    tmp=None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent,prefix='locational-update-',suffix='.tmp',delete=False) as f:
            tmp=Path(f.name);f.write(data)
        if path.read_bytes()!=original:raise ValueError('Dictionary changed while patch was prepared. No replacement made.')
        os.replace(tmp,path);tmp=None
        if path.read_bytes()!=data:raise ValueError('Post-write verification failed; original backup is preserved.')
        record['status']='APPLIED_AND_VERIFIED';log.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    finally:
        if tmp and tmp.exists():tmp.unlink()
    print('APPLIED AND VERIFIED:',path)
    print('Changed only:',TERM,'/ DICT-OCBO-055')
    print('Fields:',', '.join(CHANGES))
    print('Backup:',backupfile)
    print('Accountability log:',log)
    print('No corpus/index/benchmark files changed. Reload any process holding the old dictionary.')

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();apply(a.root)
if __name__=='__main__':main()
