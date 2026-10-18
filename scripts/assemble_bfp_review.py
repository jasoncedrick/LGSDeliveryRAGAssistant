"""Assemble reviewed BFP components in a fresh source staging version, without indices."""
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.chunk_retriever import MODEL_NAME
from src.token_windows import source_windows,verify_source_windows


def main():
    from transformers import AutoTokenizer
    previous=ROOT/'experiments/table-repairs-staged-v1'
    output=ROOT/'experiments/table-repairs-staged-v2'
    if output.exists():
        raise ValueError('Preserve existing output; use a new version')
    read=lambda p:json.loads(p.read_text(encoding='utf-8'))
    pages=read(previous/'source_pages.json')
    before=next(p for p in pages if p['source_page_id']=='BFP-PDF0001')
    text=before['text']
    start=text.index('CLIENTS STEP')
    end=text.index('CHECKLIST OF',start)
    original=text[start:end]
    cells=read(ROOT/'experiments/bfp-step2-ocr-review/procedure_cells.json')
    bag=lambda s:Counter(c for c in s if not c.isspace())
    source_cells='\n'.join(v for r in cells for v in r['text'] if v is not None)
    assert bag(original)==bag(source_cells), 'Procedure source characters differ'
    # Remove extractor-added spaces inside words; recover wording from original text.
    # Table text and source share an identical non-whitespace character inventory.
    parts=[]
    for i,row in enumerate(cells[1:],1):
        client,action,time,fee,person=row['text']
        action=action.replace('t h e details','the details').replace('F o r OSCP','For OSCP').replace('P e r m i t ( n e w/renewal)','Permit (new/renewal)')
        parts.append(f'AGENCY ROW {i}')
        if client is None:
            parts.append('CLIENTS STEP: [shared client-step 3 cell; source wording appears in agency row 3]')
        elif not client:
            parts.append('CLIENTS STEP: [blank source cell]')
        else:
            parts.append('CLIENTS STEP: '+client)
        parts.extend(['AGENCY ACTION: '+action,'PROCESSING TIME: '+time,'PERSON RESPONSIBLE: '+person])
    parts.append('FEES TO BE PAID [shared cell spanning all six agency rows]:\n'+cells[1]['text'][3])
    procedure='\n\n'.join(parts)
    poster=(ROOT/'experiments/bfp-panel-review/poster_corrected.txt').read_text(encoding='utf-8')
    after_text=text[:start]+procedure+'\n\n'+text[end:]+'\n\n[IMAGE PANEL TRANSCRIPTION — BFP PDF page 1]\n'+poster
    after=dict(before,text=after_text,text_sha256=hashlib.sha256(after_text.encode()).hexdigest())
    staged=[after if p['source_page_id']==before['source_page_id'] else p for p in pages]
    tokenizer=AutoTokenizer.from_pretrained(MODEL_NAME,local_files_only=True)
    chunks=[{**{k:v for k,v in after.items() if k not in ('text','text_sha256')},**w,
             'chunk_id':f'REVIEW-BFP-ASSEMBLED-C{i:03d}'} for i,w in enumerate(source_windows(after_text,tokenizer),1)]
    audit=verify_source_windows(chunks,[after],tokenizer)
    assert audit['passed']
    assert len(staged)==358 and sum(a!=b for a,b in zip(pages,staged))==1
    # Existing notes, matrix, forms and other text outside the procedure are untouched.
    assert after_text.startswith(text[:start])
    assert text[end:] in after_text
    for phrase in ['FCCT = 0.1%', 'FSIF = 0','1. Issue queuing number','5. Evaluation/Inspection']:
        assert after_text.count(phrase)==text.count(phrase)
    output.mkdir()
    write=lambda name,v:(output/name).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
    write('source_pages.json',staged);write('bfp_after_source_page.json',after)
    write('bfp_before_source_page.json',before);write('bfp_candidate_chunks.json',chunks)
    (output/'bfp_after.txt').write_text(after_text,encoding='utf-8')
    (output/'bfp_before_after.diff').write_text(''.join(difflib.unified_diff(text.splitlines(True),after_text.splitlines(True),fromfile='staged-v1/bfp_after.txt',tofile='staged-v2/bfp_after.txt')),encoding='utf-8')
    write('reviewer_acknowledgment.json',{'origin':'User message: g already reviewed, next pls',
          'scope':'Acknowledgment of the preceding panel transcription review; proceed with assembly.',
          'not_claimed':'Source-owner confirmation, complete transcription of cylinder microprint, or final corpus certification.',
          'prior_interpretation':read(previous/'reviewer_note.json')})
    inputs=[previous/'source_pages.json',ROOT/'experiments/bfp-panel-review/poster_corrected.txt',ROOT/'experiments/bfp-step2-ocr-review/procedure_cells.json']
    write('validation.json',{'status':'ASSEMBLED_DEVELOPMENT_SOURCE_NOT_INDEXED','pages':358,
          'changed_from_staged_v1':['BFP-PDF0001'],'unchanged_from_staged_v1':357,
          'procedure_source_character_inventory_preserved':True,'nonprocedure_text_preserved_exactly':True,
          'selected_duplicate_checks_passed':True,'token_validation':audit,
          'inputs':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
          'remaining_limits':['Photographed cylinder microprint is preserved as imagery, not fully transcribed.',
                              'Similar source warnings remain where wording differs; no broad semantic deduplication was applied.',
                              'CTO Ice Crusher missing unit remains unresolved.'],
          'app_changed':False,'indices_rebuilt':False,'benchmark_accessed':False,'frozen':False})
    print(json.dumps({'output':str(output),'token_validation':audit},indent=2))


if __name__=='__main__':
    main()
