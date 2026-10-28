"""Website-only response-language instruction, separate from frozen generation."""
import hashlib
import json
import re
from contextvars import ContextVar
from pathlib import Path
from types import FunctionType

from app.pipeline import Pipeline, ANSWER_SYSTEM_PROMPT

PROMPT_PATH = Path(__file__).resolve().parents[1]/'config/website_response_language_v2.json'
PROMPT = json.loads(PROMPT_PATH.read_text(encoding='utf-8'))
PROMPT_SHA256 = hashlib.sha256(PROMPT_PATH.read_bytes()).hexdigest()
REQUESTED_LANGUAGE = ContextVar('website_requested_response_language', default='auto')
TAGALOG = frozenset('ano paano magkano saan kailangan kelangan kailangang mga po opo ba bakit pwede puwede magpagawa magpatayo kumuha gusto magkakano gaano katagal meron ako ko'.split())
CEBUANO = frozenset('unsa asa pila tagpila kinahanglan kinahanglanon unsaon unsay asay adunay naa wala dili og ug akong imong inyong magpatukod magpahimo palihog pud gyud jud kay'.split())


def response_language(query, requested='auto'):
    if requested in ('english','taglish','bislish'):
        return requested
    if requested != 'auto':
        raise ValueError('Unsupported response language')
    tokens=set(re.findall(r"[a-z]+",query.casefold()))
    tagalog=len(tokens & TAGALOG);cebuano=len(tokens & CEBUANO)
    if cebuano>0 and cebuano>=tagalog:
        return 'bislish'
    if tagalog>0:
        return 'taglish'
    return 'english'


class WebsitePipeline(Pipeline):
    def _generate_answer(self, raw_query, retrieval):
        language=response_language(raw_query, REQUESTED_LANGUAGE.get())
        instruction=PROMPT['shared'].format(language=PROMPT[language])
        # Reuse the frozen generation implementation with a request-local globals
        # dictionary. No global patch, prompt rewrite on disk, extra LLM call,
        # post-translation, retry, or bypass of the complete-prompt byte guard.
        original=Pipeline._generate_answer
        scope={**original.__globals__, 'ANSWER_SYSTEM_PROMPT':ANSWER_SYSTEM_PROMPT+'\n'+instruction+'\n'}
        generate=FunctionType(original.__code__,scope,original.__name__,original.__defaults__,original.__closure__)
        result=generate(self,raw_query,retrieval)
        result.setdefault('diagnostics',{}).update(response_language=language,
            website_prompt_version=PROMPT['version'],website_language_prompt_sha256=PROMPT_SHA256)
        return result
