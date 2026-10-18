"""Source-coordinate repair of OCBO PDF page 14 only (printed page 502).

Writes a new review package, never changes the active corpus or indices.
Shared fee/personnel cells stay at parent-row level. No substep roles are guessed.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone, timedelta
import difflib
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.token_windows import source_windows, verify_source_windows
from src.chunk_retriever import MODEL_NAME

PDF_NAME = 'OCBD Pages from CGD_Citizen Charter 2026_VOL.I & II-2.pdf'
PDF_SHA = '6f081dde0a63ade8aaa3f4dc5a26ceb0c7fde85f896951931d8222eaa86b3093'
PAGE_ID = 'OCBO-PDF0014'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compact(text):
    return ' '.join(text.split())


def pair_actions_and_times(action_lines, time_lines, tolerance=1.0):
    """Match each substep to a single time whose first-line y coordinate agrees."""
    groups = []
    for line in sorted(action_lines, key=lambda x:x['bbox'][1]):
        if re.match(r'^\d+(?:\.\d+)?[. ]', line['text']):
            groups.append({'lines': [line]})
        elif groups:
            groups[-1]['lines'].append(line)
        else:
            raise ValueError('Action continuation has no numbered parent')
    if len(groups) != len(time_lines):
        raise ValueError('Action/time count mismatch; manual review required')
    used = set()
    for group in groups:
        anchor = group['lines'][0]['bbox'][1]
        matches = [i for i, line in enumerate(time_lines) if abs(line['bbox'][1]-anchor) <= tolerance]
        if len(matches) != 1 or matches[0] in used:
            raise ValueError('Ambiguous action/time alignment; manual review required')
        i = matches[0]; used.add(i)
        group.update(action=compact(' '.join(x['text'] for x in group['lines'])),
                     processing_time=time_lines[i]['text'], time_line=time_lines[i],
                     alignment_delta_points=abs(time_lines[i]['bbox'][1]-anchor))
    return groups


def inside(line, box):
    x0,y0,x1,y1 = line['bbox']
    return box[0] <= (x0+x1)/2 <= box[2] and box[1] <= (y0+y1)/2 <= box[3]


def extract_table(page):
    tables = page.find_tables().tables
    if len(tables) != 1 or tables[0].row_count != 2 or tables[0].col_count != 5:
        raise ValueError('Expected two source rows and five columns; manual review required')
    table = tables[0]
    cells = table.extract()
    lines = []
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines', []):
            text = ''.join(span['text'] for span in line['spans']).strip()
            if text:
                lines.append({'text': text, 'bbox': list(line['bbox'])})
    rows = []
    for i, values in enumerate(cells):
        boxes = table.rows[i].cells
        if any(box is None for box in boxes):
            raise ValueError('Unexpected merged geometry; manual review required')
        actions = [line for line in lines if inside(line, boxes[1])]
        times = [line for line in lines if inside(line, boxes[3])]
        pairs = pair_actions_and_times(actions, times)
        rows.append({'client_step': compact(values[0]),
                     'fees_to_be_paid': values[2],
                     'person_responsible_cell': values[4],
                     'agency_actions': pairs,
                     'source_cells': [{'column': name, 'text': value, 'bbox': list(box)}
                         for name,value,box in zip(
                             ['CLIENT STEPS','AGENCY ACTION','FEES TO BE PAID',
                              'PROCESSING TIME','PERSON RESPONSIBLE'], values, boxes)],
                     'personnel_substep_assignment': 'not_inferred',
                     'fee_scope': 'parent_source_cell_not_distributed'})
    return rows


def serialize(rows):
    parts = []
    for row in rows:
        parts.append('CLIENT STEPS: '+row['client_step'])
        parts.append('FEES TO BE PAID (shared source cell for this client step): '+row['fees_to_be_paid'])
        for action in row['agency_actions']:
            parts.append('AGENCY ACTION: '+action['action']+'\nPROCESSING TIME: '+action['processing_time'])
        parts.append('PERSON RESPONSIBLE (shared source cell; no individual substep assignment):\n'
                     + row['person_responsible_cell'])
    return '\n\n'.join(parts)


def main(output):
    import fitz
    from transformers import AutoTokenizer

    output = Path(output).resolve()
    if ROOT not in output.parents or output.exists():
        raise ValueError('Use a new output directory inside the repository')
    source_dir = ROOT/'experiments/chapter3-step2-development'
    pdf = ROOT/'data/raw_charters'/PDF_NAME
    if digest(pdf) != PDF_SHA:
        raise ValueError('Source PDF changed; repeat source review')
    pages = json.loads((source_dir/'source_pages.json').read_text(encoding='utf-8'))
    before = next(p for p in pages if p['source_page_id'] == PAGE_ID)
    assert before['source_page'] == 502 and before['pdf_relative_page'] == 14
    protected = [ROOT/'app/pipeline.py', ROOT/'data/municipal_dictionary_v1.json',
                 *[p for p in source_dir.iterdir() if p.is_file()]]
    hashes = {str(p.relative_to(ROOT)): digest(p) for p in protected}
    with fitz.open(pdf) as document:
        page = document[13]
        rows = extract_table(page)
        # Compare source cell content with the original stored extraction, excluding whitespace.
        char_bag = lambda t: Counter(c for c in t if not c.isspace())
        cells_text = '\n'.join(c['text'] for row in rows for c in row['source_cells'])
        if char_bag(cells_text) != char_bag(before['text']):
            raise ValueError('Source cell extraction loses or duplicates characters')
        # Ensure serialization keeps each action/time string in its original source column.
        for row in rows:
            if char_bag(' '.join(a['action'] for a in row['agency_actions'])) != char_bag(row['source_cells'][1]['text']):
                raise ValueError('Action text was changed')
            if char_bag(' '.join(a['processing_time'] for a in row['agency_actions'])) != char_bag(row['source_cells'][3]['text']):
                raise ValueError('Time text was changed')
        after_text = serialize(rows)
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, local_files_only=True)
        after = dict(before, text=after_text, text_sha256=hashlib.sha256(after_text.encode()).hexdigest())
        chunks = [{**{k:v for k,v in after.items() if k not in ('text','text_sha256')}, **window,
                   'chunk_id': f'REVIEW-OCBO-PDF0014-C{i:03d}'}
                  for i,window in enumerate(source_windows(after_text, tokenizer),1)]
        audit = verify_source_windows(chunks, [after], tokenizer)
        output.mkdir(parents=True, exist_ok=False)
        page.get_pixmap(matrix=fitz.Matrix(2,2)).save(output/'source_page14.png')
        # Render annotations in memory; the original PDF is never saved/modified.
        for row in rows:
            for action in row['agency_actions']:
                for line in [action['lines'][0], action['time_line']]:
                    page.draw_rect(fitz.Rect(line['bbox']), color=(0,0.5,0), width=0.7)
        page.get_pixmap(matrix=fitz.Matrix(2,2)).save(output/'alignment_evidence.png')
    write = lambda name,value:(output/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    write('before_source_page.json', before)
    write('after_source_page.json', after)
    write('structured_table.json', {'source_pdf':str(pdf),'pdf_sha256':PDF_SHA,
          'pdf_relative_page':14,'printed_page':502,
          'column_labels_source':'OCBO PDF page 13, printed page 501 (table header)',
          'rows':rows,'editorial_labels':'Shared-cell labels describe representation, not additional charter requirements.'})
    write('candidate_chunks.json', chunks)
    (output/'before.txt').write_text(before['text'],encoding='utf-8')
    (output/'after.txt').write_text(after_text,encoding='utf-8')
    diff=''.join(difflib.unified_diff(before['text'].splitlines(keepends=True),after_text.splitlines(keepends=True),
                                    fromfile='before.txt',tofile='after.txt'))
    (output/'before_after.diff').write_text(diff,encoding='utf-8')
    assert all(digest(ROOT/name)==sha for name,sha in hashes.items())
    write('review_record.json',{'created_at':datetime.now(timezone(timedelta(hours=8))).isoformat(),
          'status':'PAGE14_CANDIDATE_VERIFIED_WITH_SHARED_CELLS_PRESERVED',
          'source_characters_preserved':True,'numeric_and_unit_text_unchanged':True,
          'action_time_alignment':'Each time aligned within 1 PDF point of the numbered action first line',
          'token_validation':audit,'protected_file_hashes':hashes,'active_files_modified':False,
          'indices_rebuilt':False,'benchmark_accessed':False,'independent_human_review':False,
          'manual_checks':[{'item':'Person responsible for each of substeps 2.1-2.4',
                            'reason':'Source has one undivided personnel cell with repeated titles; no unique substep assignment is established.',
                            'handling':'Preserved verbatim at parent client-step level; no guessed individual assignments.',
                            'needed_before':'Any future attempt to assign personnel to individual substeps'},
                           {'item':'Confirm shared-cell representation and action/time pairs against page 502',
                            'reason':'Independent human review is not established by automated checks or assistant visual review.',
                            'needed_before':'Final source-fidelity sign-off'}]})
    print(json.dumps({'output':str(output),'paired_actions':[(a['action'],a['processing_time']) for row in rows for a in row['agency_actions']],
                      'token_validation':audit,'active_files_modified':False},indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True)
    main(parser.parse_args().output)
