"""Preserve and serialize CTO page 6 fee cells into an isolated review package."""
import argparse
from collections import Counter
import difflib
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repair_ocbo_page14 import compact, digest, inside
from src.chunk_retriever import MODEL_NAME
from src.token_windows import source_windows, verify_source_windows

PDF_NAME = "City Treasurer's CGD_Citizen Charter 2026_VOL.I & II-2.pdf"
PDF_SHA = 'b492eb8d220d1d9fb8b1d3acad2bba254d711e227063853415182b1715e546de'


def pair_fee_lines(labels, fees):
    if len(labels)!=len(fees):
        raise ValueError('Fee/label count mismatch')
    used=set()
    pairs=[]
    for label in labels:
        matches=[i for i,fee in enumerate(fees) if abs(label['bbox'][1]-fee['bbox'][1])<=1]
        if len(matches)!=1 or matches[0] in used:
            raise ValueError('Ambiguous fee alignment; manual review required')
        i=matches[0]; used.add(i)
        pairs.append({'label':label,'fee':fees[i]})
    return pairs


def main(output):
    import fitz
    from transformers import AutoTokenizer
    output=Path(output).resolve()
    if ROOT not in output.parents or output.exists():
        raise ValueError('Use a fresh output directory within the repository')
    pdf=ROOT/'data/raw_charters'/PDF_NAME
    if digest(pdf)!=PDF_SHA:
        raise ValueError('Source PDF changed')
    source_dir=ROOT/'experiments/chapter3-step2-development'
    protected=[pdf,ROOT/'app/pipeline.py',ROOT/'data/municipal_dictionary_v1.json',
               *[p for p in source_dir.iterdir() if p.is_file()]]
    hashes={str(p.relative_to(ROOT)):digest(p) for p in protected}
    before=next(p for p in json.loads((source_dir/'source_pages.json').read_text(encoding='utf-8'))
                if p['source_page_id']=='CTO-PDF0006')
    assert before['pdf_relative_page']==6 and before['source_page']==161
    with fitz.open(pdf) as doc:
        page=doc[5]
        tables=page.find_tables().tables
        assert len(tables)==1 and tables[0].row_count==9 and tables[0].col_count==2
        table=tables[0]; cells=table.extract()
        bag=lambda text:Counter(c for c in text if not c.isspace())
        assert bag('\n'.join(v for row in cells for v in row))==bag(before['text'])
        lines=[{'text':''.join(s['text'] for s in line['spans']).strip(),'bbox':list(line['bbox'])}
               for block in page.get_text('dict')['blocks'] for line in block.get('lines',[])]
        lines=[x for x in lines if x['text']]
        pairs=pair_fee_lines(
            sorted([x for x in lines if inside(x,table.rows[0].cells[0])],key=lambda x:x['bbox'][1]),
            sorted([x for x in lines if inside(x,table.rows[0].cells[1])],key=lambda x:x['bbox'][1]))
        assert len(pairs)==5
        assert bag(' '.join(p['label']['text'] for p in pairs))==bag(cells[0][0])
        assert bag(' '.join(p['fee']['text'] for p in pairs))==bag(cells[0][1])
        parts=[]
        for pair in pairs:
            # Keep Hogs and its two printed subcategories together in source order.
            parts.append('ITEM: '+pair['label']['text']+'\nFEE: '+pair['fee']['text'])
        for label,fee in cells[1:]:
            parts.append('ITEM OR HEADING: '+compact(label)+'\nFEE: '+
                         (compact(fee) if fee else '[blank source cell]'))
        text='\n\n'.join(parts)
        after=dict(before,text=text,text_sha256=hashlib.sha256(text.encode()).hexdigest())
        tokenizer=AutoTokenizer.from_pretrained(MODEL_NAME,local_files_only=True)
        chunks=[{**{k:v for k,v in after.items() if k not in ('text','text_sha256')},**w,
                 'chunk_id':f'REVIEW-CTO-PDF0006-C{i:03d}'}
                for i,w in enumerate(source_windows(text,tokenizer),1)]
        audit=verify_source_windows(chunks,[after],tokenizer)
        assert audit['passed']
        output.mkdir(parents=True)
        page.get_pixmap(matrix=fitz.Matrix(2,2)).save(output/'source_page6.png')
        for pair in pairs:
            for line in (pair['label'],pair['fee']):
                page.draw_rect(fitz.Rect(line['bbox']),color=(0,0.5,0),width=0.7)
        page.get_pixmap(matrix=fitz.Matrix(2,2)).save(output/'alignment_evidence.png')
        structured={'pdf_sha256':PDF_SHA,'source_pdf':str(pdf),'pdf_relative_page':6,'printed_page':161,
                    'first_row_pairs':pairs,'rows':[{'cells':[{'text':v,'bbox':list(b)}
                    for v,b in zip(row,geometry.cells)]} for row,geometry in zip(cells,table.rows)],
                    'editorial_labels':'ITEM, ITEM OR HEADING, FEE and [blank source cell] are representation labels.',
                    'hierarchy_note':'b. Others remains the indented second Hogs subcategory; original text and coordinates retained.'}
    write=lambda name,data:(output/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    write('before_source_page.json',before); write('after_source_page.json',after)
    write('structured_table.json',structured); write('candidate_chunks.json',chunks)
    (output/'before.txt').write_text(before['text'],encoding='utf-8')
    (output/'after.txt').write_text(text,encoding='utf-8')
    (output/'before_after.diff').write_text(''.join(difflib.unified_diff(
        before['text'].splitlines(True),text.splitlines(True),fromfile='before.txt',tofile='after.txt')),encoding='utf-8')
    assert all(digest(ROOT/p)==sha for p,sha in hashes.items())
    write('review_record.json',{'status':'CANDIDATE_WITH_INCOMPLETE_SOURCE_RATE_NOT_FINAL_SIGNOFF',
          'source_characters_preserved':True,'protected_file_hashes':hashes,'token_validation':audit,
          'active_files_modified':False,'indices_rebuilt':False,'benchmark_accessed':False,
          'independent_human_review':False,'manual_checks':[
              'Ice Crusher source reads P 10.00 per with no following unit. Obtain authoritative clarification before supplying a complete rate.',
              'Independent human sign-off on fee associations and retained heading/subcategory structure.'],
          'preserved_conditions':'Chicken: 500.00per 1,000 heads or a fraction thereof retained verbatim apart from line breaks.',
          'blank_handling':'Two empty fee cells remain explicitly blank, not zero or free.',
          'scope':'No currency or per-head unit added to the five continuation rates at top of page.'})
    print(json.dumps(audit,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    main(parser.parse_args().output)
