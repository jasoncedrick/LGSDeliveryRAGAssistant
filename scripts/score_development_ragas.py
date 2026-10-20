"""Offline local RAGAS scoring of archived development interactions; no serving filter."""
import argparse
import csv
import copy
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def finite_score(value):
    try:return float(value) if math.isfinite(float(value)) else None
    except (ValueError,TypeError):return None


def main(args):
    import torch
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import faithfulness,context_precision,context_recall,answer_relevancy
    from ragas.run_config import RunConfig
    from ragas.llms import LangchainLLMWrapper
    from langchain_community.llms import Ollama
    from langchain_core.callbacks import BaseCallbackHandler
    source=ROOT/'experiments'/args.input_name
    if args.input_subdir:
        if args.input_subdir not in ('A','B','C'):raise ValueError('Only paired A/B/C subfolders are supported')
        source=source/args.input_subdir
    output=ROOT/'experiments'/args.output_name
    if any(Path(n).name!=n for n in [args.input_name,args.output_name]) or output.exists():raise ValueError('Use experiment names and fresh output')
    protocol_path=source/'protocol.json'
    if not protocol_path.exists():protocol_path=source/'summary.json'
    protocol=json.loads(protocol_path.read_text(encoding='utf-8'))
    if protocol.get('held_out_accessed') is not False:raise ValueError('Only development archives accepted')
    if Path(args.archive_file).name!=args.archive_file:raise ValueError('Use an archive filename')
    archive=source/args.archive_file
    records=[json.loads(line) for line in archive.read_text(encoding='utf-8').splitlines()]
    selected=[r for r in records if not args.record_id or r['record_id']==args.record_id]
    if not selected:raise ValueError('No matching archived record')
    output.mkdir()
    write=lambda name,value:(output/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    class AuditCallback(BaseCallbackHandler):
        def on_llm_start(self,serialized,prompts,**kwargs):
            self.save({'event':'judge_prompt','prompts':prompts})
        def on_llm_end(self,response,**kwargs):
            self.save({'event':'judge_output','outputs':[[g.text for g in group] for group in response.generations]})
        def on_llm_error(self,error,**kwargs):self.save({'event':'judge_error','error':str(error)})
        def save(self,value):
            value['record_id']=current_record_id
            with (output/'judge_calls.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(value,ensure_ascii=False)+'\n')
    current_record_id=None
    judge=LangchainLLMWrapper(Ollama(model='eboss-mistral',base_url='http://localhost:11434',temperature=0,top_p=0,
                                   num_ctx=8192,num_predict=args.judge_output_tokens,num_thread=4,timeout=args.judge_timeout))
    metrics_by_name={k:copy.deepcopy(v) for k,v in {'faithfulness':faithfulness,'context_precision':context_precision,'context_recall':context_recall,'answer_relevancy':answer_relevancy}.items()}
    format_contract=None
    if args.strict_metric_json:
        from src.ragas_output_contracts import apply_contracts
        format_contract=apply_contracts(metrics_by_name)
    faithfulness_schema_instruction=None
    if args.strict_faithfulness_json:
        faithfulness_schema_instruction={
            'statements':'Return exactly one JSON object with the single key "statements", containing a nonempty array of strings. Decompose only the supplied answer. Stop after that object. Do not continue examples or add unrelated questions.',
            'verdicts':'Return only a JSON array with exactly one object per supplied statement in its original order. Each object must include the original statement, a reason, and "verdict" as the string "0" or "1". Do not use fractional verdicts. Do not change or negate the statement being judged. Stop after the array.'}
        metrics_by_name['faithfulness'].long_form_answer_prompt.instruction+=' '+faithfulness_schema_instruction['statements']
        metrics_by_name['faithfulness'].nli_statements_message.instruction+=' '+faithfulness_schema_instruction['verdicts']
    recall_schema_instruction=None
    if args.strict_recall_json:
        recall_schema_instruction=('Return ONLY the classification value as a top-level JSON array. '
            'Each array element must contain a statement, reason, and the exact key "Attributed" with value "1" or "0". '
            'Do not wrap the array in question, answer, classification, or any other object. Do not include markdown.')
        metrics_by_name['context_recall'].context_recall_prompt.instruction+=' '+recall_schema_instruction
    context_precision_evaluator={'version':'original_ragas_prompt','format_retry_limit':0}
    if args.context_precision_v2:
        from src.ragas_context_precision_v2 import GroundedContextPrecision
        from src.context_precision_judge_v2 import VERSION,PROMPT_TEMPLATE
        metric=GroundedContextPrecision()
        metric.format_retry_limit=1
        metric.audit_sink=lambda value: AuditCallback().save(value)
        metrics_by_name['context_precision']=metric
        context_precision_evaluator={'version':VERSION,'prompt_template_sha256':hashlib.sha256(PROMPT_TEMPLATE.encode()).hexdigest(),'format_retry_limit':1,'contract_failures':'Recorded in judge_calls.jsonl; final invalid outputs remain null','status':'Opt-in development-calibrated evaluator; not independent expert validation'}
    embeddings=None
    if 'answer_relevancy' in args.metrics:
        from langchain_core.embeddings import Embeddings
        from sentence_transformers import SentenceTransformer
        from huggingface_hub import snapshot_download
        from ragas.embeddings import LangchainEmbeddingsWrapper
        from src.chunk_retriever import MODEL_NAME
        model=SentenceTransformer(snapshot_download(MODEL_NAME,local_files_only=True),device='cpu')
        class CachedEmbeddings(Embeddings):
            def embed_documents(self,texts):return model.encode(texts,normalize_embeddings=True).tolist()
            def embed_query(self,text):return self.embed_documents([text])[0]
        embeddings=LangchainEmbeddingsWrapper(CachedEmbeddings())
    write('protocol.json',{'scope':'Offline archived development evaluation; no runtime filtering or final benchmark claims',
          'ragas_version':importlib.metadata.version('ragas'),'judge_model':'eboss-mistral','metrics':args.metrics,
          'input_archive':str(archive),'input_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
          'record_ids':[r['record_id'] for r in selected],'generation_failures_retained_in_original_archive':True,
          'reference':'Archived reference answer if available, otherwise source evidence fragments; preserve declared reference status.',
          'same_generator_and_judge_model':True,'max_workers':1,'max_retries':0,'held_out_accessed':False,
          'judge_output_tokens':args.judge_output_tokens,'judge_timeout':args.judge_timeout,
          'faithfulness_schema_instruction':faithfulness_schema_instruction,
          'context_precision_evaluator':context_precision_evaluator,
          'context_recall_schema_instruction':recall_schema_instruction,
          'metric_output_contract':format_contract})
    scored=[]
    for r in selected:
        current_record_id=r['record_id']
        item={'record_id':r['record_id'],'generation_status':r['status'],'scores':{},
              'language':r.get('language'),'group_id':r.get('question_group_id'),'pillar':r.get('pillar')}
        reference=r.get('reference_answer') or '\n'.join(' '.join(group) for group in r.get('reference_evidence_groups',[]))
        item['reference_status']=r.get('reference_status','unspecified')
        if r.get('status')!='ANSWERED' or not r.get('answer') or not reference:
            item.update(status='NOT_SCORED',reason='Requires completed answer and reference; original record retained')
        else:
            data={'question':[r['question']],'answer':[r['answer']],
                  'contexts':[[c['text'] for c in r['citations']]],
                  'ground_truth':[reference]}
            write('dataset_'+r['record_id']+'.json',data)
            try:
                result=evaluate(Dataset.from_dict(data),metrics=[metrics_by_name[m] for m in args.metrics],
                                llm=judge,embeddings=embeddings,callbacks=[AuditCallback()],
                                run_config=RunConfig(timeout=args.judge_timeout,max_retries=0,max_workers=1),raise_exceptions=False,is_async=False)
                item['scores']={name:finite_score(result.scores[0].get(name)) for name in args.metrics}
                item['status']='SCORED' if all(v is not None for v in item['scores'].values()) else 'PARTIAL_OR_FAILED_JUDGE'
            except Exception as error:item.update(status='SCORING_ERROR',scores={m:None for m in args.metrics},error_type=type(error).__name__,error=str(error))
        scored.append(item);write('scores.json',scored)
        print(json.dumps(item),flush=True)
    with (output/'scores.csv').open('w',newline='',encoding='utf-8') as f:
        fields=['record_id','generation_status','status']+args.metrics
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for r in scored:writer.writerow({**{k:r.get(k) for k in fields[:3]},**r['scores']})
    aggregates={}
    for metric in args.metrics:
        valid=[r['scores'][metric] for r in scored if r['scores'].get(metric) is not None]
        aggregates[metric]={'valid_scores':len(valid),'mean_on_valid_scores':sum(valid)/len(valid) if valid else None,
                           'failed_scores':sum(r['status']!='NOT_SCORED' and r['scores'].get(metric) is None for r in scored)}
    write('summary.json',{'selected':len(scored),'fully_scored':sum(r['status']=='SCORED' for r in scored),
          'not_scored':sum(r['status']=='NOT_SCORED' for r in scored),
          'failed_or_partial':sum(r['status'] in ('SCORING_ERROR','PARTIAL_OR_FAILED_JUDGE') for r in scored),
          'metric_aggregates':aggregates,'results':scored,
          'limits':['Local 7B judge may fail structured-output parsing; null scores are not zeros.',
                    'Same-model judging can introduce bias.','Means exclude nulls and skipped records; inspect metric-specific denominators.',
                    'Reference provenance is recorded per interaction; source review and user interpretation do not constitute independent expert certification.',
                    'Generation K and configuration are recorded in the source protocol; development scoring is not frozen held-out evaluation or independent expert certification.']})
    write('hashes.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.is_file()})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input-name',required=True);p.add_argument('--output-name',required=True)
    p.add_argument('--record-id');p.add_argument('--metrics',nargs='+',choices=['faithfulness','context_precision','context_recall','answer_relevancy'],default=['faithfulness','context_precision'])
    p.add_argument('--archive-file',default='interactions.jsonl')
    p.add_argument('--input-subdir',choices=['A','B','C'],help='Paired development configuration folder')
    p.add_argument('--judge-output-tokens',type=int,default=1024)
    p.add_argument('--judge-timeout',type=int,default=90)
    p.add_argument('--context-precision-v2',action='store_true',help='Opt-in separated-evidence judge with one audited format retry; original evaluator remains default')
    p.add_argument('--strict-faithfulness-json',action='store_true',help='Evaluator-only schema retry; retain original failed scores')
    p.add_argument('--strict-metric-json',action='store_true',help='Opt-in versioned format instructions for precision and relevancy; preserve original outputs')
    p.add_argument('--strict-recall-json',action='store_true',help='Versioned evaluator-only JSON schema instruction; retain earlier failures')
    main(p.parse_args())
