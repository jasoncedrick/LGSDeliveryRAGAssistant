"""Change only DICT-OCBO-052, preserve other file text, back up and log."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import os

TERM='occupancy permit'
CHANGES={
    'verified_english_definition':'OCBO Occupancy Permit (Certificate of Occupancy), required before a building or structure, or a portion thereof, is used or occupied, or when its existing use or occupancy classification changes.',
    'polysemy_flag':False,
    'disambiguation_rule':'',
    'curation_source':'manual; Davao City Citizens Charter 2026, OCBO, Issuance of Occupancy Permit, printed pages 501-504, PDF-relative pages 13-16'
}
def digest(data):return hashlib.sha256(data).hexdigest()
def apply(root):
    root=Path(root).resolve();path=root/'data/municipal_dictionary_v1.json'
    original=path.read_bytes();bom=original.startswith(b'\xef\xbb\xbf');text=original.decode('utf-8-sig')
    dictionary=json.loads(text);old=dictionary[TERM]
    if old.get('term_id')!='DICT-OCBO-052':raise ValueError('Unexpected term ID. No file modified.')
    if all(old.get(k)==v for k,v in CHANGES.items()):
        print('Already applied: DICT-OCBO-052. No changes made.');return
    if old.get('verified_english_definition')!='Certificate of Occupancy' or old.get('polysemy_flag') is not True:
        raise ValueError('This entry differs from the reviewed original. No file modified; send the current entry.')
    matches=list(re.finditer(r'(?m)^([ \t]*)"occupancy permit"\s*:\s*',text))
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
    backup=root/'backups'/('occupancy-dictionary-'+stamp)
    logdir=root/'experiments/dictionary-changes'/('occupancy-'+stamp)
    backup.mkdir(parents=True,exist_ok=False);logdir.mkdir(parents=True,exist_ok=False)
    backupfile=backup/path.name;shutil.copy2(path,backupfile)
    record={'status':'PREPARED','created_utc':datetime.now(timezone.utc).isoformat(),
        'target':str(path),'backup':str(backupfile),'entry':TERM,'term_id':'DICT-OCBO-052',
        'before_file_sha256':digest(original),'after_file_sha256':digest(data),
        'changes':{k:{'before':old.get(k),'after':v} for k,v in CHANGES.items()},
        'reason':'The supplied OCBO service definition supports one occupancy-permit meaning; Contract of Lease is a distinct document, not an evidenced alternate meaning of this term.',
        'source':'OCBD Pages from CGD_Citizen Charter 2026_VOL.I & II-2.pdf; printed pages 501-504, PDF-relative pages 13-16',
        'review_basis':'User-supplied source screenshots and matching PDF text; no independent domain-review approval asserted.',
        'other_dictionary_entries_changed':False,'corpus_changed':False,'indexes_rebuilt':False,'benchmarks_changed':False}
    log=logdir/'change_log.json';log.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    tmp=None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent,prefix='occupancy-update-',suffix='.tmp',delete=False) as f:
            tmp=Path(f.name);f.write(data)
        if path.read_bytes()!=original:raise ValueError('Dictionary changed while patch was prepared. No replacement made.')
        os.replace(tmp,path);tmp=None
        if path.read_bytes()!=data:raise ValueError('Post-write verification failed; original backup is preserved.')
        record['status']='APPLIED_AND_VERIFIED';log.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    finally:
        if tmp and tmp.exists():tmp.unlink()
    print('APPLIED AND VERIFIED:',path)
    print('Changed only:',TERM,'/ DICT-OCBO-052')
    print('Fields:',', '.join(CHANGES))
    print('Backup:',backupfile)
    print('Accountability log:',log)
    print('No corpus/index/benchmark files changed. Reload any process holding the old dictionary.')

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();apply(a.root)
if __name__=='__main__':main()
