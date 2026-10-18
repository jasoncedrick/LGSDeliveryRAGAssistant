"""Versioned intent checks on saved normalization outputs; no model or retrieval calls."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import argparse
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.run_normalization_fidelity_suite import checks

INTENTS={
    'occupancy-receipt':'duration',
    'locational-three-storeys':'quantity',
    'renewal-representative':'document_requirement',
    'hog-fee':'fee_amount',
    'working-days-condition':'time_unit_alternative',
    'two-storey-not-three':'requirements',
    'underspecified-22':'requirements',
    'underspecified-23':'duration',
    'underspecified-24':'fee_amount',
}


def intent_failures(intent,text):
    """Necessary intent signals only; they do not establish semantic faithfulness."""
    text=' '.join(text.split())
    failures=[]
    positive={
        'duration':r'how long|how much time|how many (?:working |business |calendar )?(?:minutes|hours|days|weeks|months)|\bduration\b|\bprocessing time\b|\btime (?:needed|required|taken)\b',
        'quantity':r'how many|\bnumber of\b|\bquantity\b',
        'document_requirement':r'\b(?:what|which)\b.*\b(?:document|documents|authorization|authority|paper|papers)\b',
        'fee_amount':r'how much|\b(?:what|which)\b.*\b(?:fee|cost|charge|amount|payment|price|settlement)\b',
        'time_unit_alternative':r'\b(?:working|business) days\b.*\bor\b.*\bcalendar days\b|\bcalendar days\b.*\bor\b.*\b(?:working|business) days\b',
        'requirements':r'\b(?:what|which)\b.*\b(?:requirements|documents|papers)\b',
    }
    if intent not in positive:return ['intent_not_specified']
    if not re.search(positive[intent],text,re.I):failures.append('missing_question_intent:'+intent)
    if intent=='duration' and re.search(r'in what order|\bsequence\b|which.*first|what.*first',text,re.I):
        failures.append('duration_changed_to_sequence')
    if intent=='quantity' and re.search(r'how much.*(?:cost|fee|pay)',text,re.I):
        failures.append('quantity_changed_to_cost')
    if intent=='fee_amount' and re.search(r'where.*(?:pay|payment)|how.*(?:make|submit).*payment',text,re.I):
        failures.append('fee_changed_to_payment_location_or_method')
    return failures


def main(candidate_folder='normalization-fidelity-suite-v2-reviewed-prompt', output_name='normalization-intent-rescore-v1'):
    if any(Path(name).name != name for name in (candidate_folder,output_name)):
        raise ValueError('Use experiment directory names')
    output=ROOT/'experiments'/output_name
    if output.exists():raise ValueError('Preserve previous scoring version')
    output.mkdir()
    write=lambda name,data:(output/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    candidate=ROOT/'experiments'/candidate_folder
    # Keep the human NF02 correction as provenance even when scoring a later run.
    review=ROOT/'experiments/normalization-fidelity-suite-v2-reviewed-prompt/human_review_template.json'
    shutil.copy2(review,output/'human_review_snapshot.json')
    reviewed=json.loads((output/'human_review_snapshot.json').read_text(encoding='utf-8-sig'))
    nf02=next(x for x in reviewed if x['id']=='NF-02')
    assert nf02['human_verdict']=='meaning_changed'
    all_results=[];summary=[];inputs={}
    for variant,folder in [('baseline','normalization-fidelity-suite-v1'),('candidate',candidate_folder)]:
        directory=ROOT/'experiments'/folder
        cases=json.loads((directory/'cases.json').read_text(encoding='utf-8'))
        saved=json.loads((directory/'results.json').read_text(encoding='utf-8'))
        by_id={c['id']:c for c in cases}
        inputs.update({str((directory/name).relative_to(ROOT)):digest(directory/name) for name in ['cases.json','results.json']})
        annotated=[{**c,'expected_question_intent':INTENTS.get(c['question_group_id'],'dictionary_clarification')} for c in cases]
        write(variant+'_cases.json',annotated)
        scores=[]
        for result in saved:
            case=by_id[result['id']]
            original=checks(case,result['response'])
            intent=INTENTS.get(case['question_group_id'])
            errors=[]
            if case['expected_status']=='SUCCESS':
                if result['response']['status']=='SUCCESS':
                    errors=intent_failures(intent,result['response'].get('normalized_query') or '')
                else:errors=['translation_unavailable_for_intent_check']
            failures=original['automatic_failures']+errors
            if case['expected_status']=='FALLBACK_TRIGGERED' and result.get('translation_api_calls')!=0:
                failures.append('translation_called_before_clarification')
            row={'variant':variant,'id':case['id'],'query':case['query'],'expected_intent':intent,
                 'actual_translation':result['response'].get('normalized_query'),
                 'original_automatic_failures':original['automatic_failures'],'intent_failures':errors,
                 'all_automatic_failures':failures,'automatic_checks_passed':not failures,
                 'semantic_review':'pending except explicitly supplied reviewer verdicts'}
            scores.append(row);all_results.append(row)
        summary.append({'variant':variant,'cases':len(scores),'original_probe_passes':sum(not x['original_automatic_failures'] for x in scores),
                        'passes_with_intent_checks':sum(x['automatic_checks_passed'] for x in scores),
                        'intent_flagged_ids':[x['id'] for x in scores if x['intent_failures']]})
    write('results.json',all_results)
    write('summary.json',{'status':'SAVED_OUTPUT_RESCORE_NEW_ACCEPTANCE_CRITERIA','summary':summary,
          'nf02_review':nf02,'methodology':'The scorer observes normalization outputs offline; it does not change translation, dictionary ambiguity fallback or retrieval.',
          'limits':['Intent expressions are incomplete lexical probes, not a bilingual semantic judge.','Strengthened checks were motivated by development errors; this is not an independent generalization estimate.','Original scores and model outputs are preserved.','Other pending and uncertain reviewer verdicts remain unapproved.'],
          'inputs':inputs,'model_calls':0,'runtime_changed':False,'retrieval_changed':False,'benchmarks_accessed':False})
    write('hashes.json',{p.name:digest(p) for p in output.iterdir() if p.is_file()})
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate-folder',default='normalization-fidelity-suite-v2-reviewed-prompt')
    parser.add_argument('--output-name',default='normalization-intent-rescore-v1')
    args=parser.parse_args();main(args.candidate_folder,args.output_name)
