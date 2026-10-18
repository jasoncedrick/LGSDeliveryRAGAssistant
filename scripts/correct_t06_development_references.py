"""Version five source-reviewed development labels and rescore immutable saved rankings.

No inference, retrieval, index rebuild, held-out access or RAGAS execution.
Evidence choices are specified from source review before reading archived rankings.
"""
import copy
import csv
from collections import Counter
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.development_retrieval_metrics import ranking_metrics


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def specifications():
    # Each sentence is a reference claim, linked to source-reviewed corpus chunks.
    return {
        'SCENARIO-BB-006': [
            ('The ICAB checklist includes an ISP contract, certification or current receipt of payment; half-closed cubicles not more than 5 feet from the floor apply to Internet Cafes only.', ['BB-PDF0079-C004']),
            ('Lighting must be at least 25 Lux for fluorescent/LED lights or 50 Lux for incandescent lights.', ['BB-PDF0080-C001']),
            ('A warning sign at least 12 x 18 inches must state: no pornography, no gambling, no hacking, no minors prior to 6:00 AM and beyond 9:00 PM, and students may not play games during prescribed school hours.', ['BB-PDF0080-C001']),
            ('A system must block or filter pornographic sites/content; permanently fixed webcams are required for Internet Cafes only.', ['BB-PDF0080-C001', 'BB-PDF0080-C002']),
            ('The checklist also prohibits selling and consuming intoxicating drinks and cigarettes on the premises and lists a copy of ICAB ordinances 227-04, 0387-12 and 0270-15, as amended.', ['BB-PDF0080-C002']),
            ('Headphones, a urinal for 30 units and below, and separate male and female CRs for 31 units and above are listed for Internet Cafes only.', ['BB-PDF0080-C002']),
            ('For Internet Cafe and Pisonet owners, the fee cell states "PHP100.00 for the first 10 units and PHP10.00 for every unit". This wording is preserved without interpreting "every unit" as "each additional unit".', ['BB-PDF0081-C002']),
        ],
        'SCENARIO-CPDO-001': [
            ('The CPDO Zoning Enforcement Division issues Zoning Certification based on the Integrated Zoning Ordinance (2019-2028).', ['CPDO-PDF0002-C001']),
            ('The checklist requires: Certified True Copy of Title(s), 1 photocopy, from the Registry of Deeds; duly accomplished application form, 1 original, from CPDO; Subdivision/Sketch Plan, 1 original, from Bureau of Land/private Geodetic Engineer; Order of Payment, 1 original, from CPDO; and Official Receipt, 1 original, from the City Treasurer\'s Office.', ['CPDO-PDF0002-C002']),
            ('The zoning fee is PHP 750 per hectare; the payment step depends on CTO processing time, described as uncontrollable time.', ['CPDO-PDF0002-C004']),
            ('The charter lists a TOTAL processing time of 3 Days, 6 Hours, and 50 Minutes.', ['CPDO-PDF0004-C001']),
        ],
        'SCENARIO-BFP-001': [
            ('The documentary checklist specifies three (3) sets of the listed documents.', ['BFP-PDF0001-C052']),
            ('The FSEC column marks architectural, civil, electrical, mechanical, plumbing, electronics, sanitary and fire protection documents.', ['BFP-PDF0001-C027', 'BFP-PDF0001-C028', 'BFP-PDF0001-C029', 'BFP-PDF0001-C030', 'BFP-PDF0001-C031']),
            ('Documents mean design plans, calculations and specifications signed and sealed by the Professional Engineer/Architect.', ['BFP-PDF0001-C032']),
            ('Also listed for FSEC are one signed-and-sealed set of the estimated value of the building/structure or facilities, including materials and labor cost, and copies of valid PRC Professional Licenses of all involved professionals.', ['BFP-PDF0001-C035', 'BFP-PDF0001-C036']),
            ('The FSEC application fee is PHP 200.00; FCCT is 0.1% of the verified estimated materials-and-labor value of the building/structure or facility, capped at PHP 50,000.00.', ['BFP-PDF0001-C017', 'BFP-PDF0001-C018']),
            ('The fee note states that, when the UAF declared estimate differs substantially from current acceptable market construction cost per square meter or the value indicated in Table II.G.1 of PD 1096, the higher value will be adopted.', ['BFP-PDF0001-C018', 'BFP-PDF0001-C019']),
        ],
        'SCENARIO-BFP-004': [
            ('FSCR/FSCCR/FSMR are required if the building/facilities/structures are required to install any or a combination of wet standpipe, automatic fire suppression, or automatic fire detection and alarm systems.', ['BFP-PDF0001-C043']),
            ('FSCR consists of plans, specifications and design analysis per building, prepared and duly signed by the Engineer/Architect-of-Record and his/her Fire Safety Practitioner.', ['BFP-PDF0001-C004']),
            ('FSCCR compiles approved submittals, test and acceptance forms for fire protection and life safety features as part of as-built documents turned over by the contractor to the owner; it is duly signed by the Contractor/Construction Manager and his/her Fire Safety Practitioner.', ['BFP-PDF0001-C004', 'BFP-PDF0001-C005']),
            ('FSMR is prepared by the building owner, his/her fire safety practitioner or authorized representative, and duly signed by the Building Administrator and his/her Fire Safety Practitioner during regular annual fire safety inspection.', ['BFP-PDF0001-C005']),
            ('The matrix associates FSCR with FSEC, FSCCR with occupancy FSIC, and FSMR with new business without valid occupancy-stage FSIC and the two renewal columns; blank cells are not exemption statements.', ['BFP-PDF0001-C040', 'BFP-PDF0001-C041', 'BFP-PDF0001-C042']),
        ],
        'SCENARIO-BFP-005': [
            ('Fire Safety Clearance for welding, cutting and other hot work operations shall be secured if required.', ['BFP-PDF0001-C043']),
            ('Per Project Duration applies to new construction or renovation; the clearance should be applied for during construction after the conduct of fire safety inspection.', ['BFP-PDF0001-C044']),
            ('Annual applies to business establishments requiring almost daily repair or maintenance due to the nature of their business or operations.', ['BFP-PDF0001-C044']),
            ('The matrix marks the per-project row under FSEC and the annual row under the two renewal columns; blank cells are not exemption statements.', ['BFP-PDF0001-C044', 'BFP-PDF0001-C045']),
        ],
    }


def main():
    previous = ROOT/'experiments/t06-formal-development-validation-v2'
    archive = ROOT/'experiments/t06-30group-development-batch-v1'
    artifacts = ROOT/'experiments/chapter3-table-repaired-development-v1'
    output = ROOT/'experiments/t06-formal-development-validation-v3'
    if output.exists():
        raise ValueError('Preserve the existing version; choose a fresh output version.')
    manuscript = Path('D:/thesis/20260923.pdf')
    tracker = Path('C:/Users/User/Downloads/thesis_progress_tracker.xlsx')
    protected = [previous/'focused_source_review.json', previous/'development_groups.derived.json',
                 ROOT/'data/benchmark_scenarios_dev.json', archive/'interactions.jsonl', archive/'protocol.json',
                 ROOT/'app/pipeline.py', ROOT/'src/chunk_retriever.py', ROOT/'src/query_normalizer.py',
                 ROOT/'data/municipal_dictionary_v1.json', ROOT/'config/normalization_intent_candidate.txt', manuscript, tracker]
    protected += list(p for p in artifacts.iterdir() if p.is_file())
    protected += list((ROOT/'data/raw_charters').glob('*.pdf'))
    hashes = {str(p): sha(p) for p in protected}
    groups = read(previous/'development_groups.derived.json')
    before = copy.deepcopy(groups)
    chunks = {c['chunk_id']: c for c in read(artifacts/'corpus.json')}
    pages = {p['source_page_id']: p for p in read(artifacts/'source_pages.json')}
    protocol = read(archive/'protocol.json')
    assert sha(artifacts/'corpus.json') == protocol['artifact_hashes']['corpus']
    assert sha(artifacts/'source_pages.json') == protocol['artifact_hashes']['source_pages']
    spec = specifications()
    evidence = []
    changes = []
    # Complete label derivation before looking at any saved ranking or generated answer.
    for g in groups:
        if g['group_id'] not in spec:
            continue
        claims = []
        for n, (claim, suffixes) in enumerate(spec[g['group_id']], 1):
            supporting = []
            for suffix in suffixes:
                c = chunks['DEV120-'+suffix]
                page = pages[c['source_page_id']]
                assert page['text'][c['char_start']:c['char_end']] == c['text_content']
                assert c['pdf_sha256'] == sha(ROOT/'data/raw_charters'/c['file_source'])
                supporting.append({k: c[k] for k in ['chunk_id', 'source_page_id', 'file_source', 'pdf_relative_page',
                                  'source_page', 'pdf_sha256', 'char_start', 'char_end', 'text_content']})
            claims.append({'claim_id': f"{g['group_id']}-CLAIM-{n:02}", 'claim': claim,
                           'support_type': 'source-reviewed; multiple chunks may be jointly necessary',
                           'supporting_chunks': supporting})
        old = {k: g[k] for k in ['ground_truth_reference_answer', 'ground_truth_chunk_ids', 'mapping_status']}
        g['ground_truth_reference_answer'] = ' '.join(c['claim'] for c in claims)
        g['ground_truth_chunk_ids'] = list(dict.fromkeys(c['chunk_id'] for claim in claims for c in claim['supporting_chunks']))
        g['mapping_status'] = 'ASSISTANT_SOURCE_REVIEWED_DEVELOPMENT_LABELS'
        changes.append({'group_id': g['group_id'], 'before': old, 'after': {k: g[k] for k in old}})
        evidence.append({'group_id': g['group_id'], 'reviewer': 'assistant, user-authorized; not independent expert certification', 'claims': claims})
    assert len(changes) == 5
    assert all(g['ground_truth_chunk_ids'] for g in groups)
    assert all(a['queries'] == b['queries'] for a, b in zip(before, groups))
    assert all(a == b for a, b in zip(before, groups) if a['group_id'] not in spec)
    output.mkdir()
    def write(name, value):
        (output/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    for filename in ['focused_source_review.json', 'development_groups.derived.json', 'development_groups.snapshot.json']:
        shutil.copyfile(previous/filename, output/(filename.replace('.json', '.before.json')))
    shutil.copyfile(archive/'interactions.jsonl', output/'interactions.original.jsonl')
    shutil.copyfile(archive/'protocol.json', output/'original_run_protocol.json')
    write('development_groups.derived.json', groups)
    write('claim_source_evidence.json', evidence)
    write('reference_changes.json', changes)
    old_text=(previous/'development_groups.derived.json').read_text(encoding='utf-8')
    new_text=(output/'development_groups.derived.json').read_text(encoding='utf-8')
    (output/'references.before_after.diff').write_text(''.join(difflib.unified_diff(old_text.splitlines(True),new_text.splitlines(True),fromfile='v2',tofile='v3')),encoding='utf-8')
    # Only after labels are fixed: rescore the immutable run.
    records = [json.loads(line) for line in (archive/'interactions.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(records) == len({r['record_id'] for r in records}) == 90
    lookup = {g['group_id']: g for g in groups}
    rows = []
    overlays = []
    for record in records:
        g = lookup[record['question_group_id']]
        assert record['question'] == g['queries'][record['language']]
        assert record['retrieved_rankings'].get('3', []) == record['retrieved_rankings'].get('5', [])[:3]
        for ids in record['retrieved_rankings'].values():
            assert len(ids) == len(set(ids)) and all(cid in chunks for cid in ids)
        overlay = copy.deepcopy(record)
        overlay['original_reference_answer'] = record['reference_answer']
        overlay['original_ground_truth_chunk_ids'] = record['ground_truth_chunk_ids']
        overlay['original_ranking_metrics'] = record['ranking_metrics']
        overlay['reference_answer'] = g['ground_truth_reference_answer']
        overlay['ground_truth_chunk_ids'] = g['ground_truth_chunk_ids']
        overlay['relevance_mapping_status'] = g['mapping_status']
        overlay['reference_status'] = ('assistant_source_reviewed' if g['group_id'] in spec else 'legacy_semantics_not_independently_certified')
        overlay['ranking_metrics'] = {}
        for k in (3,5):
            ids = record['retrieved_rankings'].get(str(k), [])
            m = ranking_metrics(ids,g['ground_truth_chunk_ids'],k)
            # Independent simple oracle protects denominator/rank handling.
            hits=[i for i,c in enumerate(ids[:k],1) if c in g['ground_truth_chunk_ids']]
            assert m['hit_at_k'] == int(bool(hits))
            assert m['mrr_at_k'] == (1/hits[0] if hits else 0)
            overlay['ranking_metrics'][str(k)] = m
            rows.append({'record_id': record['record_id'], 'group_id': g['group_id'], 'language': record['language'],
                         'pillar': record['pillar'], 'status': record['status'], 'k': k,
                         'label_status': g['mapping_status'], 'corrected_group': g['group_id'] in spec, **m})
        for field in ['question','answer','context','citations','retrieved_rankings','normalization','search_query','status','diagnostics']:
            assert (field in overlay) == (field in record)
            assert overlay.get(field) == record.get(field)
        overlays.append(overlay)
    (output/'interactions.corrected_references.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in overlays),encoding='utf-8')
    with (output/'per_query_metrics.csv').open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    def aggregate(selected):
        return {'queries':len(selected),'hits':sum(r['hit_at_k'] for r in selected),
                'hit_at_k':sum(r['hit_at_k'] for r in selected)/len(selected),
                'mrr_at_k':sum(r['mrr_at_k'] for r in selected)/len(selected)}
    metrics=[]
    for k in (3,5):
        kr=[r for r in rows if r['k']==k]
        entry={'k':k,'all_90':aggregate(kr),'unchanged_75':aggregate([r for r in kr if not r['corrected_group']]),
               'corrected_15':aggregate([r for r in kr if r['corrected_group']]),
               'by_language':{lang:aggregate([r for r in kr if r['language']==lang]) for lang in ['english','taglish','bislish']},
               'by_pillar':{pillar:aggregate([r for r in kr if r['pillar']==pillar]) for pillar in sorted({r['pillar'] for r in kr})}}
        metrics.append(entry)
    previous_summary=read(archive/'complete_outcome_summary/summary.json')
    for old,new in zip(previous_summary['ranking_metrics'],metrics):
        assert old['k']==new['k'] and old['denominator']==new['unchanged_75']['queries']
        assert abs(old['hit_at_k']-new['unchanged_75']['hit_at_k'])<1e-12
        assert abs(old['mrr_at_k']-new['unchanged_75']['mrr_at_k'])<1e-12
    summary={'status':'STEPS_1_TO_3_COMPLETE_DEVELOPMENT_ONLY','groups':30,'queries':90,'corrected_groups':list(spec),
             'statuses':dict(Counter(r['status'] for r in records)),'ranking_metrics':metrics,
             'policy':'Any relevant chunk gives Hit=1; reciprocal rank uses first relevant chunk. A hit is not complete-answer support. Stopped queries with no retrieval count as zero; no outcomes dropped.',
             'limitations':['Five groups have assistant source-reviewed answers; the other 25 retain provisional lexical mappings and unreviewed legacy answer semantics.',
                           '90-query scores have a different denominator from the earlier 75-query scores and are not evidence of improved retrieval.',
                           'BFP three-set label is stranded in chunks C052/C053, separated from documentary rows; source meaning verified visually, corpus unchanged.',
                           'BB fee wording remains ambiguous; no numeric extrapolation or additional-unit interpretation is approved.',
                           'Assistant review is not the independent expert audit specified by the manuscript.',
                           'This fixed candidate run is not a tuned/frozen Config A/B/C evaluation; generation was K=5 only.'],
             'ragas_run':False,'held_out_accessed':False,'app_defaults_changed':False,'freeze':False,
             'original_archive_sha256':sha(archive/'interactions.jsonl')}
    write('summary.json',summary)
    import fitz
    import openpyxl
    doc=fitz.open(manuscript)
    workbook=openpyxl.load_workbook(tracker,data_only=True,read_only=True)
    tracker_rows=[list(r) for r in workbook['Thesis Tracker'].iter_rows(values_only=True) if r and r[0] in ('T06','T07')]
    tracker_rows=json.loads(json.dumps(tracker_rows,default=str))
    write('methodology_and_tracker.json',{'manuscript_path':str(manuscript),'manuscript_sha256':sha(manuscript),
        'chapter3_evidence':[{'pdf_page':n,'printed_page':n-5,'text':doc[n-1].get_text()} for n in [28,30,32,33,34]],
        'tracker_path':str(tracker),'tracker_sha256':sha(tracker),'authoritative_tab':'Thesis Tracker','tracker_rows':tracker_rows,
        'interpretation':'T06 is the batch Hit/MRR/RAGAS harness. This work repairs development references and rescores archived rankings. T07 frozen architecture comparison is separate. Workbook status is preserved, not rewritten as new validation evidence.',
        'retrieval_constraints':{'chunk_tokens':120,'overlap_tokens':20,'scoring_unit':'chunk','k':[3,5],'configuration':'existing fixed candidate unchanged'}})
    assert all(sha(Path(p))==digest for p,digest in hashes.items())
    write('validation.json',{'passed':True,'checks':['30 groups / 90 unchanged query strings','exactly five answers and label sets corrected',
        '25 unaffected groups identical','every cited chunk exists and exactly matches source-page character offsets','source PDF hashes verified',
        '90 archived outcomes retained; answers, contexts, normalizations and rankings unchanged','180 K-specific metric rows independently checked',
        'prior 75-query metrics reproduced exactly','all protected input hashes unchanged'], 'input_hashes':hashes})
    report = ['T06 development reference correction and archived-ranking rescore', '',
              'Completed steps 1-3 only. Five answers and relevance sets were revised from the source review; all 90 original queries and generated outcomes were preserved.', '',
              'K | Queries | Hits | Hit rate | MRR']
    for m in metrics:
        a=m['all_90'];report.append(f"{m['k']} | {a['queries']} | {a['hits']} | {a['hit_at_k']:.6f} | {a['mrr_at_k']:.6f}")
    report += ['', 'Read reference_changes.json for exact before/after answers and IDs; claim_source_evidence.json maps each corrected sentence to source text, pages, offsets and hashes.', '',
               'The unchanged 75-query subset reproduces its prior metrics exactly. The full denominator is now 90, including all six clarification outcomes as misses. These scores do not measure a retrieval improvement.', '',
               *summary['limitations'], '', 'Next, on user instruction: Step 4 offline RAGAS using interactions.corrected_references.jsonl, with clarification skips and scoring failures recorded separately. Step 5 final validation report follows; neither has been run here.']
    (output/'REVIEW_REPORT.txt').write_text('\n'.join(report)+'\n',encoding='utf-8')
    write('files_sha256.json',{'created_utc':datetime.now(timezone.utc).isoformat(),
          'builder_sha256':sha(Path(__file__)), 'files':{p.name:sha(p) for p in output.iterdir() if p.is_file()}})
    print(json.dumps(summary,indent=2))


if __name__ == '__main__':
    main()
