"""Text-layer preservation audit; visual-review findings are separate evidence.

This does not certify table relationships or graphical requirements matrices.
No benchmark queries or evaluation results are read.
"""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT/'experiments/chapter3-step2-development'
OUTPUT = ROOT/'experiments/chapter3-step3-source-review'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    import fitz

    pages = json.loads((ARTIFACTS/'source_pages.json').read_text(encoding='utf-8'))
    checks = []
    for filename in sorted({p['file_source'] for p in pages}):
        path = ROOT/'data/raw_charters'/filename
        digest = sha(path)
        with fitz.open(path) as pdf:
            stored = [p for p in pages if p['file_source'] == filename]
            if {p['pdf_relative_page'] for p in stored} != set(range(1, len(pdf)+1)):
                raise ValueError(f'Incomplete PDF page coverage: {filename}')
            for record in stored:
                page = pdf[record['pdf_relative_page']-1]
                lines = []
                for block in page.get_text('rawdict')['blocks']:
                    for line in block.get('lines', []):
                        lines.append(''.join(c['c'] for span in line['spans'] for c in span['chars']))
                lines = [line.strip() for line in lines if line.strip()]
                printed = record['source_page']
                removed = None
                if printed is not None:
                    if lines[0] == str(printed):
                        removed = lines.pop(0)
                    elif lines[-1] == str(printed):
                        removed = lines.pop()
                expected, actual = '\n'.join(lines), record['text']
                chars = lambda text: Counter(c for c in text if not c.isspace())
                digits = lambda text: Counter(re.findall(r'\d+', text))
                checks.append({'source_page_id': record['source_page_id'],
                               'file_source': filename, 'pdf_relative_page': page.number+1,
                               'printed_page': printed, 'removed_page_number': removed,
                               'pdf_hash_matches': record['pdf_sha256'] == digest,
                               'non_whitespace_characters_preserved': chars(expected) == chars(actual),
                               'numeric_token_counts_preserved': digits(expected) == digits(actual),
                               'replacement_characters': actual.count('\ufffd'),
                               'vector_drawing_count': len(page.get_drawings())})
    visual = json.loads((OUTPUT/'visual_review.json').read_text(encoding='utf-8'))
    report = {'status': 'ISSUES_FOUND_NOT_SOURCE_CERTIFIED',
              'corpus_sha256': sha(ARTIFACTS/'corpus.json'),
              'source_pages_sha256': sha(ARTIFACTS/'source_pages.json'),
              'pdf_text_layer_pages_checked': len(checks),
              'pdf_text_layer_checks_passed': all(c['pdf_hash_matches'] and
                  c['non_whitespace_characters_preserved'] and c['numeric_token_counts_preserved']
                  and c['replacement_characters'] == 0 for c in checks),
              'visual_pages_reviewed': len(visual['pages']), 'visual_review': visual,
              'full_table_layout_review_complete': False,
              'suitable_for_final_freeze': False, 'benchmark_evaluation_performed': False,
              'limitation': 'Text-layer preservation does not prove row/column associations, '
                            'graphics extraction, or correct reading order. Development integration only.',
              'page_checks': checks}
    (OUTPUT/'source_fidelity_review.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('page_checks','visual_review')},indent=2))


if __name__ == '__main__':
    main()
