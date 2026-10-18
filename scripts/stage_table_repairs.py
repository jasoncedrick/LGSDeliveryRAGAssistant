"""Stage source-page repairs without building indices or changing the app."""
import difflib
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.repair_ocbo_page14 import digest


def locate(text, label):
    pattern=r'\s+'.join(re.escape(w) for w in label.split())
    matches=list(re.finditer(pattern,text))
    if len(matches)!=1:
        raise ValueError(f'Expected one source occurrence for {label!r}; got {len(matches)}')
    return matches[0].span()


def insert_annotations(text, annotations):
    spans=[]
    for label,annotation in annotations:
        start,end=locate(text,label)
        spans.append((start,end,annotation))
    spans.sort()
    if any(a[1]>b[0] for a,b in zip(spans,spans[1:])):
        raise ValueError('Overlapping source annotations')
    parts=[]; cursor=0; ledger=[]
    for start,end,annotation in spans:
        parts.append(text[cursor:end])
        addition='\n[REPRESENTATION: '+annotation+']\n'
        parts.append(addition)
        ledger.append({'original_start':start,'original_end':end,'source_text':text[start:end],'inserted_text':addition})
        cursor=end
    parts.append(text[cursor:])
    after=''.join(parts)
    restored=after
    for item in ledger:
        restored=restored.replace(item['inserted_text'],'',1)
    if restored!=text:
        raise ValueError('Original text reconstruction failed')
    return after,ledger


def main():
    import fitz
    output=ROOT/'experiments/table-repairs-staged-v1'
    if output.exists():
        raise ValueError('Output already exists; preserve prior review')
    base=ROOT/'experiments/chapter3-step2-development'
    pages=json.loads((base/'source_pages.json').read_text(encoding='utf-8'))
    before=next(p for p in pages if p['source_page_id']=='BFP-PDF0001')
    matrix_dir=ROOT/'experiments/bfp-matrix-review'
    matrix=json.loads((matrix_dir/'matrix.json').read_text(encoding='utf-8'))
    pdf=ROOT/'data/raw_charters/BFP-CITIZENS-CHARTER-2022.pdf'
    assert digest(pdf)==matrix['source_pdf_sha256']
    protected=[pdf,ROOT/'app/pipeline.py',ROOT/'data/municipal_dictionary_v1.json',*[p for p in base.iterdir() if p.is_file()]]
    hashes={str(p.relative_to(ROOT)):digest(p) for p in protected}
    annotations=[]
    for row in matrix['rows']:
        label=row['text']
        note=re.match(r'^NOTE \((\d)\) (.*)$',label)
        if note:
            label=note[2]+' NOTE ('+note[1]+')'
        columns=matrix['columns']
        marked=[c['label'] for c in columns if row['cells'][c['id']]=='dot shown']
        annotations.append((label,'Matrix dot shown for: '+'; '.join(marked)+
                             '. Other service cells are blank in source; blank is not an exemption statement.'))
    with fitz.open(pdf) as doc:
        table=doc[0].find_tables().tables[0]; values=table.extract()
        forms=[]
        for r,c,ids in [(8,3,[0]),(8,4,[1,2,3,4,5]),(9,3,[0,1]),(9,5,[2,3,4,5])]:
            label=' '.join(values[r][c].split())
            form={'text':label,'source_bbox':list(table.rows[r].cells[c]),
                  'services':[matrix['columns'][i]['label'] for i in ids]}
            forms.append(form)
            annotations.append((label,'Application-form cell spans: '+'; '.join(form['services'])+'.'))
        after_text,ledger=insert_annotations(before['text'],annotations)
        output.mkdir(parents=True)
        doc[0].get_pixmap(matrix=fitz.Matrix(0.8,0.8),clip=fitz.Rect(10,600,2580,1220)).save(output/'application_forms.png')
        # Preserve image-only material as visual evidence, not invented OCR text.
        doc[0].get_pixmap(matrix=fitz.Matrix(1,1),clip=fitz.Rect(10,4200,1300,5120)).save(output/'poster_visual_content.png')
    write=lambda name,data:(output/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    after=dict(before,text=after_text,text_sha256=hashlib.sha256(after_text.encode()).hexdigest())
    write('bfp_before_source_page.json',before);write('bfp_after_source_page.json',after)
    (output/'bfp_before.txt').write_text(before['text'],encoding='utf-8')
    (output/'bfp_after.txt').write_text(after_text,encoding='utf-8')
    (output/'bfp_before_after.diff').write_text(''.join(difflib.unified_diff(before['text'].splitlines(True),after_text.splitlines(True),fromfile='bfp_before.txt',tofile='bfp_after.txt')),encoding='utf-8')
    write('bfp_annotation_ledger.json',ledger);write('application_form_mappings.json',forms)
    write('reviewer_note.json',{'origin':'User clarification in this conversation','source_wording':matrix['rows'][8]['text'],
          'reviewer_interpretation':'The as-built plan together with the building permit is conditional on changes; the user interprets these as changes to the specific document.',
          'handling':'Source wording retained exactly. Interpretation is review metadata only, excluded from retrieval text.',
          'remaining_uncertainty':'The source excerpt does not precisely define which changes trigger the condition.',
          'screenshot_claims_added':False})
    replacements={'BFP-PDF0001':after}
    inputs={}
    for folder in ['ocbo-page14-table-repair','ocbo-page15-table-repair','cto-page6-table-repair']:
        path=ROOT/'experiments'/folder/'after_source_page.json'
        value=json.loads(path.read_text(encoding='utf-8'))
        replacements[value['source_page_id']]=value
        inputs[str(path.relative_to(ROOT))]=digest(path)
    staged=[replacements.get(p['source_page_id'],p) for p in pages]
    assert len(staged)==len(pages)==358
    assert len({p['source_page_id'] for p in staged})==358
    changed=[a['source_page_id'] for a,b in zip(pages,staged) if a!=b]
    assert set(changed)==set(replacements)
    for page in staged:
        assert hashlib.sha256(page['text'].encode()).hexdigest()==page['text_sha256']
        old=next(p for p in pages if p['source_page_id']==page['source_page_id'])
        assert all(page[k]==old[k] for k in ('file_source','pdf_relative_page','source_page','pdf_sha256'))
    write('source_pages.json',staged)
    assert all(digest(ROOT/p)==sha for p,sha in hashes.items())
    write('staging_validation.json',{'status':'DEVELOPMENT_SOURCE_STAGING_NOT_INDEXED','source_pages':358,'changed_pages':changed,
          'unchanged_pages':354,'bfp_original_text_exactly_recoverable':True,'annotations':len(ledger),
          'source_text_deleted_or_repeated':False,'application_form_mappings':len(forms),
          'reviewer_interpretation_in_retrieval_text':False,'protected_file_hashes':hashes,'repair_input_hashes':inputs,
          'indices_rebuilt':False,'app_modified':False,'benchmark_accessed':False,
          'remaining_review':['Image-only poster content is preserved visually but not fully transcribed into retrieval text; complete visual coverage cannot be certified.',
                              'Non-matrix procedure table text is preserved, but its row relationships have not been newly certified.',
                              'Final human source sign-off and CTO Ice Crusher unit clarification remain pending.'],
          'next_build_constraints':{'window_tokens':120,'overlap_tokens':20,'scoring':'chunk-level BM25-FAISS-dictionary','allowed_k':[3,5]}})
    print(json.dumps({'output':str(output),'pages':len(staged),'changed':changed,'annotations':len(ledger)}))


if __name__=='__main__':
    main()
