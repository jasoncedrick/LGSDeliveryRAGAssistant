"""Frozen development inputs for normalization only; never retrieves or generates answers."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.query_normalizer import QueryNormalizer,BASELINE_SYSTEM_PROMPT,MAX_TRANSLATION_TOKENS


def checks(case,result):
    expected=case['expected_status']
    text=result.get('normalized_query') or ''
    failures=[]
    if result.get('status')!=expected:failures.append('unexpected_status')
    if expected=='FALLBACK_TRIGGERED':
        if result.get('normalized_query') is not None:failures.append('translation_before_clarification')
        if not result.get('clarification_prompt'):failures.append('missing_clarification')
    elif result.get('status')=='SUCCESS':
        if not text.strip():failures.append('empty_translation')
        if '\n' in text or re.search(r'\b(?:Glossary|Citizen Query|Translated Query)\s*:|```',text,re.I):failures.append('extra_output')
        d=result.get('diagnostics',{})
        if d.get('done') is False or d.get('done_reason')=='length' or result.get('tokens_generated',0)>=MAX_TRANSLATION_TOKENS:failures.append('incomplete_translation')
        for name,alternatives in case.get('required_concepts',{}).items():
            if not any(re.search(pattern,text,re.I) for pattern in alternatives):failures.append('missing_concept:'+name)
        for pattern in case.get('forbidden_patterns',[]):
            if re.search(pattern,text,re.I):failures.append('forbidden_addition:'+pattern)
    return {'automatic_failures':failures,'automatic_checks_passed':not failures,
            'english_wording_preserved':(' '.join(case['query'].lower().split())==' '.join(text.lower().split())) if case['language']=='English' and expected=='SUCCESS' else None,
            'semantic_human_review':'pending; regex matches cannot prove faithful translation'}


def cases():
    groups=[
      ('occupancy-receipt',[
        'For an occupancy permit, how long does OCBO take to encode and receive documents?',
        'Para sa occupancy permit, pila ka oras ang pag-encode ug pagdawat sa mga dokumento sa OCBO?',
        'Para sa occupancy permit, gaano katagal ang pag-encode at pagtanggap ng mga dokumento sa OCBO?'],
       'How long does OCBO take to encode and receive documents for an occupancy permit?',
       {'service':[r'occupancy permit',r'certificate of occupancy'],'office':[r'\bOCBO\b'],'encoding':[r'encod'],'receiving':[r'receiv',r'receipt',r'accept']},[r'building permit',r'eBOSS']),
      ('locational-three-storeys',[
        'For CPDO locational clearance for a three-storey building, how many building-plan sets are required?',
        'Para sa CPDO locational clearance sa tulo ka andana nga building, pila ka sets sa building plans ang kinahanglan?',
        'Para sa CPDO locational clearance ng tatlong palapag na building, ilang sets ng building plans ang kailangan?'],
       'How many sets of building plans are required for CPDO locational clearance for a three-storey building?',
       {'office':[r'\bCPDO\b'],'service':[r'locational clearance'],'height':[r'three[ -]store',r'3[ -]store',r'three[ -]floor',r'3[ -]floor'],'quantity_question':[r'how many',r'number of']},[r'two[ -]store',r'2[ -]store']),
      ('renewal-representative',[
        'For business permit renewal, what authority document does a represented sole proprietor need?',
        'Sa renewal sa business permit, unsang dokumento sa awtoridad ang kinahanglan kung naay representante ang sole proprietor?',
        'Sa renewal ng business permit, anong dokumento ng awtoridad ang kailangan kung may kinatawan ang sole proprietor?'],
       'What authority document is required for a sole proprietor applying through a representative for business permit renewal?',
       {'service':[r'business permit'],'stage':[r'renew'],'ownership':[r'sole propriet'],'representation':[r'represent',r'behalf'],'question':[r'what',r'which']},[r'new business permit']),
      ('hog-fee',[
        'What is the City Treasurer fee for washing of hogs?',
        'Pila ang bayad sa City Treasurer para sa paghugas sa mga baboy?',
        'Magkano ang bayad sa City Treasurer para sa paghuhugas ng mga baboy?'],
       'What is the City Treasurer fee for washing hogs?',
       {'office':[r'city treasurer'],'fee_question':[r'how much',r'what.*fee',r'what.*cost',r'what.*charge'],'washing':[r'wash'],'animal':[r'hog',r'pig']},[r'\b10\.00\b']),
      ('working-days-condition',[
        'For business permit renewal, does the processing time use working days or calendar days?',
        'Sa renewal sa business permit, working days ba o calendar days ang processing time?',
        'Sa renewal ng business permit, working days ba o calendar days ang processing time?'],
       'For business permit renewal, is processing time counted in working days or calendar days?',
       {'service':[r'business permit'],'stage':[r'renew'],'working_days':[r'working days',r'business days'],'calendar_days':[r'calendar days'],'alternative':[r'\bor\b']},[]),
      ('two-storey-not-three',[
        'For locational clearance, what requirements apply to a two-storey building, not a three-storey building?',
        'Para sa locational clearance, unsang requirements para sa duha ka andana nga building, dili tulo ka andana?',
        'Para sa locational clearance, anong requirements para sa dalawang palapag na building, hindi tatlong palapag?'],
       'What locational clearance requirements apply to a two-storey building rather than a three-storey building?',
       {'service':[r'locational clearance'],'two':[r'two[ -]store',r'2[ -]store',r'two[ -]floor',r'2[ -]floor'],'three':[r'three[ -]store',r'3[ -]store',r'three[ -]floor',r'3[ -]floor'],'negation':[r'\bnot\b',r'rather than',r'instead of']},[]),
    ]
    result=[]
    for group,queries,reference,concepts,forbidden in groups:
        for language,query in zip(['English','Bislish','Taglish'],queries):
            result.append({'id':f'NF-{len(result)+1:02d}','question_group_id':group,'language':language,'query':query,'reference_translation':reference,'required_concepts':concepts,'forbidden_patterns':forbidden,'expected_status':'SUCCESS','reference_review':'assistant drafted; independent bilingual review pending'})
    for query in ['Unsay kinahanglan para sa resibo?','Magkano ang sedula?','What are the requirements for barangay clearance?']:
        result.append({'id':f'NF-{len(result)+1:02d}','question_group_id':'dictionary-conflict-'+str(len(result)+1),'language':'Mixed','query':query,'expected_status':'FALLBACK_TRIGGERED','reference_review':'Trigger grounded in current dictionary polysemy flags; no guessing the selected meaning.'})
    for query in ['What documents do I need for clearance?','How long does OCBO take?','How much is the permit fee?']:
        result.append({'id':f'NF-{len(result)+1:02d}','question_group_id':'underspecified-'+str(len(result)+1),'language':'English','query':query,'expected_status':'SUCCESS','required_concepts':{},'forbidden_patterns':[],'reference_review':'Missing-slot clarification is not prescribed by dictionary-conflict mechanism. Manual check for invented service scope.'})
    return result


def main(output_name, prompt_file=None):
    output=ROOT/'experiments'/output_name
    if Path(output_name).name!=output_name or output.exists():raise ValueError('Use a new directory name')
    output.mkdir()
    write=lambda name,v:(output/name).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
    inputs=cases();write('cases.json',inputs)
    prompt = Path(prompt_file).read_text(encoding='utf-8') if prompt_file else BASELINE_SYSTEM_PROMPT
    (output/'prompt.txt').write_text(prompt,encoding='utf-8')
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    write('protocol.json',{'scope':'Development normalization diagnostic only; no retrieval, answers or held-out access','english_preservation':'Exact wording equality reported as stability diagnostic; faithful grammar changes can still be semantically valid.','semantic_checks':'Predeclared regex concept probes; human semantic review remains necessary.','model_settings':{'temperature':0,'top_p':0,'num_predict':150},'context_rules':False,'fidelity_candidate':False,'prompt_override':str(prompt_file) if prompt_file else None,'cases_sha256':digest(output/'cases.json'),'dictionary_sha256':digest(ROOT/'data/municipal_dictionary_v1.json'),'normalizer_sha256':digest(ROOT/'src/query_normalizer.py'),'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest()})
    normalizer=QueryNormalizer(str(ROOT/'data/municipal_dictionary_v1.json'),enable_context_rules=False,enable_fidelity_contract=False)
    import requests
    original_post=requests.post
    results=[]
    for case in inputs:
        calls=[]
        def capture(*args,**kwargs):
            calls.append(kwargs.get('json',{}));return original_post(*args,**kwargs)
        try:
            with patch('src.query_normalizer.BASELINE_SYSTEM_PROMPT',prompt), patch('src.query_normalizer.requests.post',side_effect=capture):r=normalizer.normalize(case['query'])
        except Exception as error:r={'status':'ERROR','error':str(error)}
        record={'id':case['id'],'group':case['question_group_id'],'language':case['language'],'query':case['query'],'response':r,'translation_api_calls':len(calls),**checks(case,r)}
        if case['expected_status']=='FALLBACK_TRIGGERED' and calls:
            record['automatic_failures'].append('translation_called_before_clarification');record['automatic_checks_passed']=False
        results.append(record);write('results.json',results)
        print(case['id']+' '+r['status']+' '+str(record['automatic_failures']),flush=True)
    write('summary.json',{'status':'PROVISIONAL_DEVELOPMENT_NORMALIZATION_FIDELITY','cases':len(results),'automatic_checks_passed':sum(r['automatic_checks_passed'] for r in results),'failed_ids':[r['id'] for r in results if not r['automatic_checks_passed']],'english_exact_preservation':{'matched':sum(r['english_wording_preserved'] is True for r in results),'tested':sum(r['english_wording_preserved'] is not None for r in results)},'by_language':{language:{'cases':sum(r['language']==language for r in results),'checks_passed':sum(r['language']==language and r['automatic_checks_passed'] for r in results)} for language in sorted({r['language'] for r in results})},'human_translation_review':'pending','runtime_changed':False,'held_out_accessed':False,'limits':['Automatic concept checks cannot establish semantic fidelity or correct negation scope.','Reference translations are assistant-authored development fixtures, not human-approved ground truth.','No formal multilingual benchmark scores are claimed.']})
    write('hashes.json',{p.name:digest(p) for p in output.iterdir() if p.is_file()})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-name',default='normalization-fidelity-suite-v1')
    parser.add_argument('--prompt-file',type=Path,help='Offline development prompt override; never changes app settings')
    args=parser.parse_args();main(args.output_name,args.prompt_file)
