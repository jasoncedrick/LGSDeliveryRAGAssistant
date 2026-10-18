"""T06 development batch generation from immutable saved retrieval, without re-ranking."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def context_from_saved(row,by_id):
    k=row['k']
    if k not in (3,5) or len(row['returned'])!=k:
        raise ValueError('Expected exactly K saved chunks')
    citations=[];blocks=[];seen=set()
    for rank,item in enumerate(row['returned'],1):
        cid=item['chunk_id'];c=by_id[cid]
        if cid in seen or item['text']!=c['text_content'] or item['source_page_id']!=c['source_page_id']:
            raise ValueError('Saved context differs from indexed corpus')
        seen.add(cid);label=f'S{rank}'
        citations.append({'citation':label,'chunk_id':cid,'file_source':c['file_source'],
                          'source_page':c.get('source_page'),'pdf_relative_page':c['pdf_relative_page'],'text':item['text']})
        blocks.append(f"[{label}] {c['file_source']} | printed page {c.get('source_page')} | chunk {cid}\n{item['text']}")
    return {'context':'\n\n'.join(blocks),'citations':citations}


def main(args):
    import torch
    from app.pipeline import Pipeline,ANSWER_SYSTEM_PROMPT
    source=ROOT/'experiments/source-evidence-development-v4-intent-candidate'
    artifacts=ROOT/'experiments/chapter3-table-repaired-development-v1'
    output=ROOT/'experiments'/args.output_name
    if Path(args.output_name).name!=args.output_name or output.exists():raise ValueError('Use a fresh experiment name')
    read=lambda p:json.loads(p.read_text(encoding='utf-8'))
    questions={q['id']:q for q in read(source/'questions.json')}
    ids=args.ids.split(',') if args.ids else list(questions)
    if any(i not in questions for i in ids):raise ValueError('Unknown development ID')
    rows=[r for r in read(source/'results.json') if r['id'] in ids and r['mode'] in args.modes]
    pipeline=Pipeline(artifacts_dir=artifacts)
    if pipeline.retriever.artifact_hashes!=read(source/'summary.json')['artifact_hashes']:
        raise ValueError('Retrieval artifacts changed since saved run')
    output.mkdir()
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    protocol={'status':'DEVELOPMENT_BATCH_GENERATION','source':str(source),'ids':ids,'modes':args.modes,
              'input_hashes':{name:digest(source/name) for name in ['questions.json','results.json','normalizations.json','summary.json']},
              'artifact_hashes':pipeline.retriever.artifact_hashes,'answer_prompt_sha256':hashlib.sha256(ANSWER_SYSTEM_PROMPT.encode()).hexdigest(),
              'app_code_sha256':digest(ROOT/'app/pipeline.py'),'model':pipeline.model_name,'model_endpoint':pipeline.endpoint,
              'sampling':'Explicit development smoke subset; not formal A/B/C comparison','held_out_accessed':False,'runtime_defaults_changed':False}
    (output/'protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8')
    records=[]
    for row in rows:
        q=questions[row['id']]
        record={'record_id':f"{row['id']}-{row['mode']}-K{row['k']}",'question_id':row['id'],'question_group_id':row['id'],
                'mode':row['mode'],'k':row['k'],'question':q['query'],'search_query':row['search_query'],
                'kind':q['kind'],'reference_evidence_groups':q.get('evidence_groups',[]),
                'reference_status':'provisional development source fragments; not independent gold answer',
                'created_utc':datetime.now(timezone.utc).isoformat()}
        if row['status']!='RETRIEVED':
            record.update(status='NOT_GENERATED',generation_started=False,answer='',reason='Normalization/retrieval did not produce usable context',citations=[])
        else:
            retrieval=context_from_saved(row,pipeline.chunk_by_id)
            record.update(context=retrieval['context'],citations=retrieval['citations'])
            record.update(pipeline._generate_answer(q['query'],retrieval))
        with (output/'interactions.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(record,ensure_ascii=False)+'\n')
        records.append(record)
        print(record['record_id']+' '+record['status'],flush=True)
    from collections import Counter
    (output/'summary.json').write_text(json.dumps({'records':len(records),'statuses':dict(Counter(r['status'] for r in records)),
        'all_outputs_retained':True,'faithfulness_evaluation':'offline_pending','held_out_accessed':False},indent=2),encoding='utf-8')
    (output/'hashes.json').write_text(json.dumps({p.name:digest(p) for p in output.iterdir() if p.is_file()},indent=2),encoding='utf-8')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-name',required=True);p.add_argument('--ids',help='Comma-separated development IDs; omitted means all saved IDs')
    p.add_argument('--modes',nargs='+',choices=['raw','normalized'],default=['raw','normalized'])
    main(p.parse_args())
