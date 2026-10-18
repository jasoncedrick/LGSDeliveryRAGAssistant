"""Source-pinned BFP dot-matrix review. Matrix-only candidate, not a page replacement."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.repair_ocbo_page14 import compact,digest
from src.chunk_retriever import MODEL_NAME
from src.token_windows import source_windows,verify_source_windows


def assign_dots(dots,rows,columns):
    memberships=[[] for _ in rows]
    for dot in dots:
        x=(dot[0]+dot[2])/2; y=(dot[1]+dot[3])/2
        rs=[i for i,r in enumerate(rows) if r['y_range'][0]<y<r['y_range'][1]]
        cs=[i for i,c in enumerate(columns) if c['x_range'][0]<x<c['x_range'][1]]
        if len(rs)!=1 or len(cs)!=1:
            raise ValueError('Unassigned or ambiguous dot')
        if cs[0] in memberships[rs[0]]:
            raise ValueError('Duplicate dot in cell')
        memberships[rs[0]].append(cs[0])
    return [sorted(m) for m in memberships]


def main(output):
    import fitz
    from transformers import AutoTokenizer
    output=Path(output).resolve()
    if ROOT not in output.parents or output.exists():
        raise ValueError('Use fresh repository output directory')
    pdf=ROOT/'data/raw_charters/BFP-CITIZENS-CHARTER-2022.pdf'
    assert digest(pdf)=='4390d6ddc91d3090adc413002f4a998cba1b46e07b66d41e6b3b6caf135c5f74'
    source=ROOT/'experiments/chapter3-step2-development'
    protected=[pdf,ROOT/'app/pipeline.py',ROOT/'data/municipal_dictionary_v1.json',*[p for p in source.iterdir() if p.is_file()]]
    hashes={str(p.relative_to(ROOT)):digest(p) for p in protected}
    before=next(p for p in json.loads((source/'source_pages.json').read_text(encoding='utf-8')) if p['source_page_id']=='BFP-PDF0001')
    with fitz.open(pdf) as doc:
        page=doc[0]; table=page.find_tables().tables[0]; cells=table.extract()
        columns=[{'id':f'S{i+1}','label':compact(cells[5][3] if i==0 else cells[6][i+3]),
                  'parent_heading':None if i==0 else compact(cells[5][4]),
                  'x_range':[box[0],box[2]]} for i,box in enumerate(table.rows[12].cells[3:])]
        rows=[]
        first=cells[11][1].splitlines()
        # Individually reviewed bands in the undivided first source cell.
        bounds=[1220,1264,1311,1356,1400,1447,1492,1537,1585]
        note=compact(' '.join(first[8:-1]))
        for i in range(8):
            rows.append({'text':first[i],'y_range':bounds[i:i+2],
                         'conditions':['Three (3) set of the following documents',note]})
        rows.append({'text':first[-1],'y_range':[1680,1753.0888815487133],
                     'conditions':['Source condition is visibly truncated; no missing text supplied.']})
        for i in range(12,20):
            box=table.rows[i].cells[3]
            rows.append({'text':compact(cells[i][0] if i<15 else cells[i][2]),
                         'y_range':[box[1],box[3]],
                         'conditions':[] if i<15 else ['If applied in Fire Station/Lone District Fire Office)']})
        for i in range(21,24):
            box=table.rows[i].cells[3]
            rows.append({'text':compact(cells[i][0]),'y_range':[box[1],box[3]],
                         'conditions':[compact(cells[24][0])]})
        hot=cells[25][0]
        intro,body=hot.split('1) ',1); project,annual=body.split('2) ',1)
        rows.extend([{'text':'1) '+compact(project),'y_range':[2480.1127685546876,2656], 'conditions':[compact(intro)]},
                     {'text':'2) '+compact(annual),'y_range':[2656,2715.189995659722], 'conditions':[compact(intro)]}])
        dots=[]
        for drawing in page.get_drawings():
            r=drawing['rect']
            if 956<r.x0<2575 and 1220<r.y0<2716 and 10<r.width<45 and 10<r.height<45:
                assert drawing['fill']==(0,0,0)
                dots.append(list(r))
        assert len(dots)==35 and len(rows)==22
        membership=assign_dots(dots,rows,columns)
        # Independent transcription from rendered close-ups, not inferred from text.
        expected=[[0]]*8+[[1,2,3,4,5],[2,3,4,5],[0],[0],[1],[1],[1],[2],[2,3,4,5],[0],[1],[3,4,5],[0],[4,5]]
        assert membership==expected, [(i,a,b) for i,(a,b) in enumerate(zip(membership,expected)) if a!=b]
        parts=['BFP PDF page 1: documentary applicability matrix.\nEditorial convention: dot shown means marked in this source; blank does not establish exemption.']
        for row,marked in zip(rows,membership):
            row['cells']={c['id']:('dot shown' if i in marked else 'blank in source') for i,c in enumerate(columns)}
            parts.append('DOCUMENT: '+row['text']+'\n'+ '\n'.join('CONDITION: '+c for c in row['conditions'])
                         +'\nDOT SHOWN FOR: '+ '; '.join((columns[i]['parent_heading']+' / ' if columns[i]['parent_heading'] else '')+columns[i]['label'] for i in marked))
        text='\n\n'.join(parts)
        candidate=dict(before,text=text,text_sha256=hashlib.sha256(text.encode()).hexdigest())
        tokenizer=AutoTokenizer.from_pretrained(MODEL_NAME,local_files_only=True)
        chunks=[{**{k:v for k,v in candidate.items() if k not in ('text','text_sha256')},**w,'chunk_id':f'REVIEW-BFP-MATRIX-C{i:03d}'} for i,w in enumerate(source_windows(text,tokenizer),1)]
        audit=verify_source_windows(chunks,[candidate],tokenizer); assert audit['passed']
        output.mkdir(parents=True)
        for name,rect in [('upper',(10,600,2580,1850)),('lower',(10,1840,2580,2720))]:
            page.get_pixmap(matrix=fitz.Matrix(1,1),clip=fitz.Rect(rect)).save(output/(name+'.png'))
    write=lambda name,data:(output/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    write('before_source_page.json',before)
    write('matrix.json',{'source_pdf_sha256':digest(pdf),'pdf_relative_page':1,'columns':columns,'rows':rows,'dot_rectangles':dots})
    write('matrix_candidate_chunks.json',chunks)
    (output/'before.txt').write_text(before['text'],encoding='utf-8')
    (output/'after_matrix.txt').write_text(text,encoding='utf-8')
    original='\n'.join(v for row in cells[11:26] for v in row if v)
    (output/'before_matrix.txt').write_text(original,encoding='utf-8')
    (output/'matrix_before_after.diff').write_text(''.join(difflib.unified_diff(original.splitlines(True),text.splitlines(True),fromfile='before_matrix.txt (table extractor)',tofile='after_matrix.txt (matrix candidate)')),encoding='utf-8')
    assert all(digest(ROOT/p)==sha for p,sha in hashes.items())
    write('review_record.json',{'status':'MATRIX_ONLY_CANDIDATE_NOT_FULL_PAGE_REPLACEMENT','dot_count':35,'row_count':22,
          'service_columns':6,'cells':132,'blank_cells':97,'coordinate_membership_matches_visual_transcription':True,
          'token_validation':audit,'protected_file_hashes':hashes,'active_files_modified':False,
          'independent_human_review':False,'benchmark_accessed':False,'indices_rebuilt':False,
          'manual_checks':['As-built plan condition ends with If there is changes/; obtain authoritative complete wording.',
                           'Confirm all 132 dot/blank cells and shared conditions before final source sign-off.'],
          'remaining_integration':['Preserve application-form merged-cell mappings, full NOTE (1)-(4) definitions and all non-matrix page content when composing the rebuilt source page.',
                                   'Review image-only poster content separately; this matrix repair does not certify the complete poster.']})
    print(json.dumps({'dots':len(dots),'rows':len(rows),'token_validation':audit},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True)
    main(parser.parse_args().output)
