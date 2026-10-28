"""Website-only response-language instruction, separate from frozen generation."""
import hashlib
import json
import re
from contextvars import ContextVar
from pathlib import Path
from types import FunctionType

from app.pipeline import Pipeline, ANSWER_SYSTEM_PROMPT

PROMPT_PATH = Path(__file__).resolve().parents[1]/'config/website_response_language_v4.json'
PROMPT = json.loads(PROMPT_PATH.read_text(encoding='utf-8'))
PROMPT_SHA256 = hashlib.sha256(PROMPT_PATH.read_bytes()).hexdigest()
REQUESTED_LANGUAGE = ContextVar('website_requested_response_language', default='auto')
TAGALOG = frozenset('ano anong sino paano magkano saan kailangan kelangan kailangang mga po opo bakit pwede puwede magpagawa magpatayo kumuha gusto magkakano gaano katagal meron dadalhin pipirma'.split())
CEBUANO = frozenset('unsa asa pila tagpila kinahanglan kinahanglanon unsaon unsay asay adunay naa dili og ug akong imong inyong nako nimo ra kog mi among magpatukod magpahimo palihog pud gyud jud kay'.split())


def response_language(query, requested='auto'):
    if requested in ('english','taglish','bislish'):
        return requested
    if requested != 'auto':
        raise ValueError('Unsupported response language')
    tokens=set(re.findall(r"[a-z]+",query.casefold()))
    tagalog=len(tokens & TAGALOG);cebuano=len(tokens & CEBUANO)
    if cebuano>0:
        return 'bislish'
    if tagalog>0:
        return 'taglish'
    return 'english'


class WebsitePipeline(Pipeline):
    def handle_query(self, raw_query):
        from app.website_intake import intake_message, localize_clarification
        language=response_language(raw_query, REQUESTED_LANGUAGE.get())
        intake=intake_message(raw_query, language)
        if intake:
            status, message=intake
            return {'status':status,'raw_query':raw_query,'answer':message,
                    'clarification_prompt':message if status=='CLARIFICATION_REQUIRED' else None,
                    'citations':[], 'retrieval_started':False,'generation_started':False,
                    'diagnostics':{'response_language':language,'website_prompt_version':PROMPT['version'],
                                   'intake_rule':status,'faithfulness_evaluation':'not_applicable_ui_message'}}
        result=super().handle_query(raw_query)
        result.setdefault('diagnostics',{}).update(response_language=language,website_prompt_version=PROMPT['version'])
        if result['status']=='CLARIFICATION_REQUIRED':
            prompt=result['clarification_prompt']
            result['clarification_options']=re.findall(r'\[Option [A-Z]:\s*(.*?)\]',prompt)
            result['diagnostics']['original_clarification']=prompt
            result['answer']=result['clarification_prompt']=localize_clarification(prompt,language)
        return result

    def _generate_answer(self, raw_query, retrieval):
        language=response_language(raw_query, REQUESTED_LANGUAGE.get())
        from app.website_scope import coverage_issue
        from app.pipeline import FALLBACK_ANSWER
        issue=coverage_issue(raw_query,retrieval['citations'])
        if issue:
            return {'status':'NO_SUPPORTED_ANSWER','answer':FALLBACK_ANSWER,
                    'generation_started':False,'tokens_generated':0,
                    'diagnostics':{'coverage_issue':issue,'response_language':language,
                                   'website_prompt_version':PROMPT['version'],
                                   'faithfulness_evaluation':'not_performed_scope_check_only'}}
        instruction=PROMPT['shared'].format(language=PROMPT[language])
        # Reuse the frozen generation implementation with a request-local globals
        # dictionary. No global patch, prompt rewrite on disk, extra LLM call,
        # post-translation, retry, or bypass of the complete-prompt byte guard.
        original=Pipeline._generate_answer
        scope={**original.__globals__, 'ANSWER_SYSTEM_PROMPT':instruction+'\n'}
        generate=FunctionType(original.__code__,scope,original.__name__,original.__defaults__,original.__closure__)
        # Labels/source identity remain; internal chunk IDs are diagnostic metadata,
        # not citizen-facing facts. Pass exactly the same selected passage text.
        context='\n\n'.join(f"[{c['citation']}] {c.get('file_source','Source')} | PDF page {c.get('pdf_relative_page','unknown')}\n{c.get('text','')}" for c in retrieval['citations']) if all('text' in c for c in retrieval['citations']) else retrieval['context']
        result=generate(self,raw_query,{**retrieval,'context':context})
        result.setdefault('diagnostics',{}).update(response_language=language,
              website_prompt_version=PROMPT['version'],website_language_prompt_sha256=PROMPT_SHA256,
              generation_context=context)
        return result
