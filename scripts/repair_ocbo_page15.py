"""Isolated OCBO page 15 review candidate; never replaces active artifacts."""
import argparse
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repair_ocbo_page14 import PDF_NAME, PDF_SHA, compact, digest, inside
from src.chunk_retriever import MODEL_NAME
from src.token_windows import source_windows, verify_source_windows


def pair_spans(groups, times):
    """Accept one time within each complete action's vertical span, not nearest text."""
    if len(groups) != len(times):
        raise ValueError('Action/time count mismatch')
    used = set()
    result = []
    for group in groups:
        top = min(x['bbox'][1] for x in group)
        bottom = max(x['bbox'][3] for x in group)
        matches = [i for i,t in enumerate(times)
                   if top-1 <= (t['bbox'][1]+t['bbox'][3])/2 <= bottom+1]
        if len(matches) != 1 or matches[0] in used:
            raise ValueError('Ambiguous action/time span; manual checking required')
        i = matches[0]
        used.add(i)
        result.append({'action':compact(' '.join(x['text'] for x in group)),
                       'processing_time':times[i]['text'], 'action_lines':group,
                       'time_line':times[i]})
    return result


def main(output):
    import fitz
    from transformers import AutoTokenizer
    output = Path(output).resolve()
    if ROOT not in output.parents or output.exists():
        raise ValueError('Use a new output directory within the repository')
    pdf = ROOT/'data/raw_charters'/PDF_NAME
    if digest(pdf) != PDF_SHA:
        raise ValueError('Source PDF changed')
    source_dir = ROOT/'experiments/chapter3-step2-development'
    protected = [pdf, ROOT/'app/pipeline.py', ROOT/'data/municipal_dictionary_v1.json',
                 *[p for p in source_dir.iterdir() if p.is_file()]]
    hashes = {str(p.relative_to(ROOT)):digest(p) for p in protected}
    before = next(p for p in json.loads((source_dir/'source_pages.json').read_text(encoding='utf-8'))
                  if p['source_page_id']=='OCBO-PDF0015')
    assert before['pdf_relative_page']==15 and before['source_page']==503
    with fitz.open(pdf) as doc:
        page = doc[14]
        tables = page.find_tables().tables
        assert len(tables)==1 and tables[0].row_count==2 and tables[0].col_count==5
        table = tables[0]
        values = table.extract()
        lines = [{'text': ''.join(s['text'] for s in line['spans']).strip(), 'bbox':list(line['bbox'])}
                 for block in page.get_text('dict')['blocks'] for line in block.get('lines',[])]
        lines = [line for line in lines if line['text']]
        rows = []
        parts = []
        bag = lambda text: Counter(c for c in text if not c.isspace())
        assert bag('\n'.join(v for row in values for v in row))==bag(before['text'])
        for index, cells in enumerate(values):
            boxes = table.rows[index].cells
            actions = sorted([x for x in lines if inside(x,boxes[1])],key=lambda x:x['bbox'][1])
            times = sorted([x for x in lines if inside(x,boxes[3])],key=lambda x:x['bbox'][1])
            groups = []
            heading = []
            for line in actions:
                start = line['text'].startswith('·') if index==0 else bool(re.match(r'^4\.\d+ ',line['text']))
                if start:
                    groups.append([line])
                elif groups:
                    groups[-1].append(line)
                else:
                    heading.append(line)
            assert len(groups)==6
            if index==1:
                assert not heading
            pairs = pair_spans(groups,times)
            assert bag(' '.join(x['text'] for x in heading)+' '.join(p['action'] for p in pairs))==bag(cells[1])
            assert bag(' '.join(p['processing_time'] for p in pairs))==bag(cells[3])
            rows.append({'source_cells':[{'text':v,'bbox':list(b)} for v,b in zip(cells,boxes)],
                         'heading':heading,'pairs':pairs,'personnel_substep_assignment':'not_inferred'})
            parts.extend(['CLIENT STEPS: '+compact(cells[0]),
                          'FEES TO BE PAID (shared source cell for this client step): '+cells[2]])
            if heading:
                parts.append('AGENCY ACTION: '+compact(' '.join(x['text'] for x in heading)))
            for pair in pairs:
                parts.append(('INSPECTION CATEGORY: ' if index==0 else 'AGENCY ACTION: ')+pair['action']
                             +'\nPROCESSING TIME: '+pair['processing_time'])
            parts.append('PERSON RESPONSIBLE (shared source cell; no individual substep assignment):\n'+cells[4])
        text = '\n\n'.join(parts)
        after = dict(before,text=text,text_sha256=hashlib.sha256(text.encode()).hexdigest())
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME,local_files_only=True)
        chunks = [{**{k:v for k,v in after.items() if k not in ('text','text_sha256')},**w,
                   'chunk_id':f'REVIEW-OCBO-PDF0015-C{i:03d}'}
                  for i,w in enumerate(source_windows(text,tokenizer),1)]
        audit = verify_source_windows(chunks,[after],tokenizer)
        assert audit['passed']
        output.mkdir(parents=True)
        page.get_pixmap(matrix=fitz.Matrix(2,2)).save(output/'source_page15.png')
        for row in rows:
            for pair in row['pairs']:
                for line in pair['action_lines']+[pair['time_line']]:
                    page.draw_rect(fitz.Rect(line['bbox']),color=(0,0.5,0),width=0.7)
        page.get_pixmap(matrix=fitz.Matrix(2,2)).save(output/'alignment_evidence.png')
    write = lambda name,data:(output/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    write('before_source_page.json',before)
    write('after_source_page.json',after)
    write('candidate_chunks.json',chunks)
    write('structured_table.json',{'source_pdf':str(pdf),'pdf_sha256':PDF_SHA,'pdf_relative_page':15,
          'printed_page':503,'columns':['CLIENT STEPS','AGENCY ACTION','FEES TO BE PAID','PROCESSING TIME','PERSON RESPONSIBLE'],
          'headers_from':'PDF page 13, printed 501','rows':rows,
          'editorial_labels':'Shared-cell and inspection-category labels describe representation only.'})
    (output/'before.txt').write_text(before['text'],encoding='utf-8')
    (output/'after.txt').write_text(text,encoding='utf-8')
    (output/'before_after.diff').write_text(''.join(difflib.unified_diff(
        before['text'].splitlines(True),text.splitlines(True),fromfile='before.txt',tofile='after.txt')),encoding='utf-8')
    assert all(digest(ROOT/p)==sha for p,sha in hashes.items())
    write('review_record.json',{'status':'CANDIDATE_ASSISTANT_REVIEW_NOT_FINAL_SIGNOFF',
          'protected_file_hashes':hashes,'source_characters_preserved':True,'token_validation':audit,
          'active_files_modified':False,'indices_rebuilt':False,'benchmark_accessed':False,
          'independent_human_review':False,
          'manual_checks':['Confirm personnel assignments with source owner before assigning them to individual categories or substeps.',
                           'Independent human review of action/time relationships before final source-fidelity sign-off.'],
          'preserved_conditions':'Client and/or authorized representative must be present on-site; exact source wording retained.',
          'blanks':'No blank spacing interpreted as zero, None, or a new value.',
          'time_semantics':'Six 2 Days entries preserved individually; no total duration inferred.'})
    print(json.dumps(audit,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    main(parser.parse_args().output)
