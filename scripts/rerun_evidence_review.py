"""Version current development labels and compare raw/normalized chunk retrieval."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import argparse
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.evaluate_source_evidence_dev import covers,normalize


def main(output_name='source-evidence-development-v2', fidelity_contract=False, prompt_file=None, questions_file=None):
    import torch
    from app.pipeline import Pipeline
    source=ROOT/'experiments/source-evidence-development-v1'
    if Path(output_name).name != output_name:
        raise ValueError('Output name must be a directory name')
    output=ROOT/'experiments'/output_name
    if output.exists():
        raise ValueError('Use fresh output; previous runs are preserved')
    output.mkdir()
    write=lambda name,v:(output/name).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    shutil.copy2(questions_file or source/'questions.json',output/'questions.input_snapshot.json')
    shutil.copy2(source/'user_review_20261019.json',output/'user_review.json')
    questions=json.loads((output/'questions.input_snapshot.json').read_text(encoding='utf-8'))
    directory=ROOT/'experiments/chapter3-table-repaired-development-v1'
    pages={p['source_page_id']:p for p in json.loads((directory/'source_pages.json').read_text(encoding='utf-8'))}
    corrections=[]; validations=[]
    for q in questions:
        if q['kind']!='answerable':
            continue
        page=pages[q['source_page_id']]
        assert page['file_source']==q['file_source'] and page['pdf_relative_page']==q['pdf_relative_page']
        for group in q['evidence_groups']:
            for i,fragment in enumerate(group):
                if not covers(page['text'],[fragment]):
                    # Only the known source spacing change; never fabricate a missing label.
                    candidate=fragment.replace('500.00 per','500.00per')
                    if candidate==fragment or not covers(page['text'],[candidate]):
                        raise ValueError(f"Source does not support {q['id']}: {fragment}")
                    corrections.append({'id':q['id'],'before':fragment,'after':candidate,'reason':'Match printed source spacing; numerical value and unit unchanged.'})
                    group[i]=candidate
        validations.append({'id':q['id'],'page':q['source_page_id'],'printed_page':page['source_page'],
                            'all_fragments_found':True,'evidence_groups':q['evidence_groups'],
                            'scope_validation':'Source and prior visual reviews support label; row association and independent review remain separate from substring validation.'})
    write('questions.json',questions);write('label_validation.json',validations);write('label_corrections.json',corrections)
    label_hash=digest(output/'questions.json')
    pipeline=Pipeline(artifacts_dir=directory)
    pipeline.normalizer.enable_fidelity_contract = fidelity_contract
    from src.query_normalizer import BASELINE_SYSTEM_PROMPT
    prompt=Path(prompt_file).read_text(encoding='utf-8') if prompt_file else BASELINE_SYSTEM_PROMPT
    if prompt_file and fidelity_contract:
        raise ValueError('Choose a prompt override or fidelity-contract candidate, not both')
    (output/'prompt.txt').write_text(prompt,encoding='utf-8')
    results=[];normalizations=[]
    for q in questions:
        try:
            with patch('src.query_normalizer.BASELINE_SYSTEM_PROMPT',prompt):
                n=pipeline.normalizer.normalize(q['query'])
        except Exception as error:
            n={'status':'ERROR','error_type':type(error).__name__,'error':str(error)}
        normalizations.append({'id':q['id'],'raw_query':q['query'],**n})
        write('normalizations.json',normalizations)
        for mode,query in [('raw',q['query']),('normalized',n.get('normalized_query') if n['status']=='SUCCESS' else None)]:
            for k in (3,5):
                row={'id':q['id'],'kind':q['kind'],'mode':mode,'k':k,'search_query':query}
                if not isinstance(query,str) or not query.strip():
                    row.update(status='NOT_RETRIEVED',normalization_status=n['status'])
                else:
                    response=pipeline.retriever.retrieve(query,top_k=k)
                    chunks=[pipeline.chunk_by_id[x] for x in response['source_chunk_ids']]
                    row.update(status='RETRIEVED',returned=[{'chunk_id':c['chunk_id'],'source_page_id':c['source_page_id'],'text':c['text_content']} for c in chunks])
                    if q['kind']=='answerable':
                        eligible=[c for c in chunks if c['source_page_id']==q['source_page_id']]
                        groups=[[c['chunk_id'] for c in eligible if covers(c['text_content'],g)] for g in q['evidence_groups']]
                        row.update(page_hit=bool(eligible),evidence_group_chunk_ids=groups,all_evidence_groups_covered=all(groups))
                results.append(row)
        write('results.json',results)
        print(q['id']+' '+n['status'],flush=True)
    summaries=[]
    for mode in ('raw','normalized'):
        for k in (3,5):
            rows=[r for r in results if r['kind']=='answerable' and r['mode']==mode and r['k']==k]
            summaries.append({'mode':mode,'k':k,'answerable':len(rows),'retrieved':sum(r['status']=='RETRIEVED' for r in rows),'page_hits':sum(r.get('page_hit',False) for r in rows),'evidence_hits':sum(r.get('all_evidence_groups_covered',False) for r in rows),'misses':[r['id'] for r in rows if not r.get('all_evidence_groups_covered',False)]})
    context=[]
    for q in questions:
        if q['kind']!='answerable':continue
        matching=[c for c in pipeline.retriever.chunks if c['source_page_id']==q['source_page_id'] and any(covers(c['text_content'],g) for g in q['evidence_groups'])]
        context.append({'id':q['id'],'evidence_chunks':[{'chunk_id':c['chunk_id'],'text':c['text_content']} for c in matching],
                        'service_terms_to_review':q['query'],'note':'Human/assistant semantic comparison required; absent literal service wording alone does not prove retrieval causation.'})
    write('source_context.json',context)
    assert label_hash==digest(output/'questions.json')
    write('summary.json',{'status':'DEVELOPMENT_DIAGNOSTIC_NOT_FINAL_EVALUATION','summary':summaries,'label_hash':label_hash,
          'artifact_hashes':pipeline.retriever.artifact_hashes,'normalization_configuration':{'dictionary_injection':True,'context_rules':False,'fidelity_contract':fidelity_contract,'prompt_override':str(prompt_file) if prompt_file else None,'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'mistral_settings_changed':False},
          'answer_generation_performed':False,'benchmarks_accessed':False,'weights_changed':False,
          'limits':['Evidence fragments are lexical checks, not proof of row relationship or answer correctness.','English-only diagnostic questions; not the manuscript formal grouped multilingual evaluation.','Ambiguous cases have no unique target and are excluded from answerable hit counts.']})
    write('run_hashes.json',{p.name:digest(p) for p in output.iterdir() if p.is_file()})
    print(json.dumps(summaries,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-name',default='source-evidence-development-v2')
    parser.add_argument('--fidelity-contract',action='store_true',help='Opt into development normalization candidate')
    parser.add_argument('--prompt-file',type=Path,help='Offline candidate only; never changes app default')
    parser.add_argument('--questions-file',type=Path,help='Use frozen development labels from a prior run')
    args=parser.parse_args()
    main(args.output_name,args.fidelity_contract,args.prompt_file,args.questions_file)
