"""Small assistant-labelled development diagnostic; never loads held-out questions."""
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def normalize(text):
    return ' '.join(text.lower().split())


def covers(text, fragments):
    return all(normalize(fragment) in normalize(text) for fragment in fragments)


def main():
    import torch
    from app.pipeline import Pipeline
    output=ROOT/'experiments/source-evidence-development-v1'
    if output.exists():
        raise ValueError('Keep prior development results immutable')
    directory=ROOT/'experiments/chapter3-table-repaired-development-v1'
    pages={p['source_page_id']:p for p in json.loads((directory/'source_pages.json').read_text(encoding='utf-8'))}
    specs=[
      ('OCBO','OCBO-PDF0014','For an occupancy permit, how long does OCBO take to encode and receive documents?',
       [['2.1 Encode and receive documents','PROCESSING TIME: 5 Minutes']]),
      ('OCBO','OCBO-PDF0015','For an occupancy permit, how long is the structural inspection and assessment?',
       [['Structural','PROCESSING TIME: 2 Days']]),
      ('OCBO','OCBO-PDF0015','During an occupancy permit inspection, who must be present on-site?',
       [['During the inspection','client and/or authorized representative','architect or engineer','must be present on-site']]),
      ('OCBO','OCBO-PDF0014','For an occupancy permit, how long does routing documents to zoning for validation take?',
       [['2.4 Route to zoning for validation','PROCESSING TIME: 1 Day']]),
      ('CTO','CTO-PDF0006','What is the City Treasurer fee for washing of hogs?',
       [['Washing of Hogs','10.00 per head']]),
      ('CTO','CTO-PDF0006','What is the chicken block chilling rate, including its quantity condition?',
       [['Chicken','500.00per 1,000 heads or a fraction thereof']]),
      ('BFP','BFP-PDF0001','Under the BFP charter, what happens to FSIF when the LGU or PEZA assessment is zero?',
       [['If assessment from LGUs/PEZA = 0, then','FSIF = 0']]),
      ('BFP','BFP-PDF0001','What is the BFP FSEC application fee?',
       [['For FSEC','Application Fee: Php 200.00']]),
      ('BB','BB-PDF0016','For business permit renewal, what employee information must the list include and how many copies?',
       [['RENEWAL','List of Employees stating the Name and Position of the Employees (1 copy)']]),
      ('BB','BB-PDF0016','For business permit renewal, what authority document does a represented sole proprietor need?',
       [['For Sole Proprietorship, if represented','Special Power of Attorney','specific authority and capacity'],['Special Power of Attorney','notarized by any Notary Public']]),
      ('CPDO','CPDO-PDF0011','For locational clearance for a three-storey building, how many building-plan sets are needed and how must they be prepared?',
       [['Seven (7) complete sets of Building Plans (original copy)','Filled-up title blocks','Signed and sealed by CE / Architect']]),
      ('CPDO','CPDO-PDF0011','Who may apply for building locational clearance for three storeys and above?',
       [['Who may avail','Building Owner or Authorized Representative']]),
    ]
    questions=[]
    for i,(office,page,query,groups) in enumerate(specs,1):
        assert all(covers(pages[page]['text'],g) for g in groups),(page,groups)
        questions.append({'id':f'DEV-EVID-{i:02d}','kind':'answerable','office':office,'query':query,
                          'source_page_id':page,'file_source':pages[page]['file_source'],
                          'pdf_relative_page':pages[page]['pdf_relative_page'],'printed_page':pages[page]['source_page'],
                          'evidence_groups':groups,'human_label_review':'pending'})
    for query,missing in [('How long does OCBO take to encode and receive documents?','Permit/service type'),
                          ('How long is the structural inspection?','Office and permit/service type'),
                          ('What documents do I need for clearance?','Clearance type and application stage'),
                          ('How much is the permit fee?','Issuing office and permit type')]:
        questions.append({'id':f'DEV-EVID-{len(questions)+1:02d}','kind':'ambiguous','query':query,
                          'missing_context':missing,'evidence_groups':[],
                          'expected_behavior':'Seek missing context or qualify service scope; no unique target page assigned.',
                          'human_label_review':'pending'})
    output.mkdir()
    write=lambda name,data:(output/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    write('questions.json',questions)
    label_hash=hashlib.sha256((output/'questions.json').read_bytes()).hexdigest()
    pipeline=Pipeline(artifacts_dir=directory)
    results=[]
    for q in questions:
        for k in (3,5):
            response=pipeline.retriever.retrieve(q['query'],top_k=k)
            chunks=[pipeline.chunk_by_id[x] for x in response['source_chunk_ids']]
            result={'id':q['id'],'k':k,'kind':q['kind'],'query':q['query'],
                    'returned':[{'chunk_id':c['chunk_id'],'source_page_id':c['source_page_id'],'text':c['text_content']} for c in chunks]}
            if q['kind']=='answerable':
                eligible=[c for c in chunks if c['source_page_id']==q['source_page_id']]
                evidence=[[c['chunk_id'] for c in eligible if covers(c['text_content'],g)] for g in q['evidence_groups']]
                all_source=[c for c in pipeline.retriever.chunks if c['source_page_id']==q['source_page_id']]
                result.update(page_hit=bool(eligible),evidence_group_chunk_ids=evidence,
                              all_evidence_groups_covered=all(evidence),
                              groups_available_in_any_corpus_chunk=[any(covers(c['text_content'],g) for c in all_source) for g in q['evidence_groups']],
                              semantic_service_scope_review='pending; same-page lexical matches are not semantic proof')
            else:
                result['clarification_behavior']='not evaluated: retrieval-only run; no generation call'
            results.append(result)
    summaries=[]
    for k in (3,5):
        subset=[r for r in results if r['k']==k and r['kind']=='answerable']
        summaries.append({'k':k,'answerable_questions':len(subset),'page_hits':sum(r['page_hit'] for r in subset),
                          'complete_lexical_evidence_hits':sum(r['all_evidence_groups_covered'] for r in subset),
                          'misses':[r['id'] for r in subset if not r['all_evidence_groups_covered']]})
    write('results.json',results)
    write('summary.json',{'status':'PROVISIONAL_ASSISTANT_LABELLED_DEVELOPMENT_DIAGNOSTIC','summary':summaries,
          'questions_sha256':label_hash,'artifact_hashes':pipeline.retriever.artifact_hashes,
          'label_review_pending':True,'ambiguous_questions':4,'normalization_or_generation_evaluated':False,
          'scoring':'All fragments within each evidence group must co-occur in one returned chunk of the labelled source page; groups may use different returned chunks.',
          'limits':['Not a representative or balanced benchmark: OCBO has four cases, other offices two each.',
                    'Lexical coverage does not prove correct table relationship or service scope; inspect returned evidence manually.',
                    'Labels prepared before this run but by the same assistant, not an independent annotator.',
                    'No parameter tuning, held-out access, or app switch.'],
          'manual_review':['Confirm questions identify the intended service and expected source facts, including units and conditions.',
                           'Verify BB renewal notarization belongs to the correct row, not a similar earlier checklist item.',
                           'Check partial or split evidence and incorrect-service results before treating hits as adequate answers.',
                           'Review ambiguous-query labels; generation must be tested separately for clarification behavior.']})
    print(json.dumps(summaries,indent=2))


if __name__=='__main__':
    main()
