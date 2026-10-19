from pathlib import Path
import json, hashlib, re, difflib
ROOT=Path('experiments/source-reference-review-remaining-batch-v1')
REF=Path('experiments/t06-formal-development-validation-v3/development_groups.derived.json')
CORP=Path('experiments/chapter3-table-repaired-development-v1/corpus.json')
groups=json.loads(REF.read_text(encoding='utf-8')); corpus=json.loads(CORP.read_text(encoding='utf-8'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(s):return ''.join(c.lower() for c in s if c.isalnum())
def evidence(office,page,start,end):
 rows=[r for r in corpus if r['source_page_id']==f'{office}-PDF{page:04d}']; assert rows
 chars=[' ']*max(r['char_end'] for r in rows)
 for r in rows:chars[r['char_start']:r['char_end']]=r['text_content']
 text=''.join(chars); pos=[i for i,c in enumerate(text) if c.isalnum()]; cleaned=norm(text); a=cleaned.index(norm(start)); b=cleaned.index(norm(end),a)+len(norm(end)); lo=pos[a]; hi=pos[b-1]+1
 return {'source_page_id':rows[0]['source_page_id'],'pdf_relative_page':page,'printed_page':rows[0]['source_page'],'source_span':text[lo:hi],'char_start':lo,'char_end':hi,'supporting_chunk_ids':[r['chunk_id'] for r in rows if r['char_start']<hi and r['char_end']>lo]}
def review(group_id,claims,findings,manual=None,status='needs_correction'):
 g=next(x for x in groups if x['group_id']==group_id);office=group_id.split('-')[1]; out=ROOT/group_id;out.mkdir(exist_ok=True); mapped=[]
 for text,spans in claims:
  ev=[evidence(office,*s) for s in spans]; mapped.append({'claim':text,'evidence':ev,'supporting_chunk_ids':list(dict.fromkeys(i for e in ev for i in e['supporting_chunk_ids']))})
 ids=list(dict.fromkeys(i for r in mapped for i in r['supporting_chunk_ids'])); answer='\n\n'.join(c[0] for c in claims)
 candidate=dict(g,ground_truth_reference_answer=answer,ground_truth_chunk_ids=ids,mapping_status='ASSISTANT_SOURCE_REVIEWED_CANDIDATE_NOT_APPLIED')
 for n,data in [('group.before.json',g),('group.candidate.json',candidate),('claim_source_map.json',mapped),('review.json',{'group_id':group_id,'review_status':status,'reviewer':'assistant','findings':findings,'manual_check':manual,'candidate_applied':False,'limitations':['Fixed thesis sources, not present-day legal advice.','Assistant image review is not independent expert certification.','Supporting IDs use overlap with explicitly reviewed source spans; an individual ID need not contain the complete answer.']} )]:write(out/n,data)
 (out/'reference_candidate.txt').write_text(answer+'\n',encoding='utf-8');(out/'before_after.diff').write_text(''.join(difflib.unified_diff(json.dumps(g,ensure_ascii=False,indent=2).splitlines(True),json.dumps(candidate,ensure_ascii=False,indent=2).splitlines(True),fromfile='group.before.json',tofile='group.candidate.json')),encoding='utf-8')
 write(out/'artifact_hashes.json',{p.name:digest(p) for p in out.iterdir() if p.is_file() and p.name!='artifact_hashes.json'})
 print(group_id,status,len(mapped),'claims')
