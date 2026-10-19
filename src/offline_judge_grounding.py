"""Experimental offline evaluator contract; not imported by the serving pipeline."""
import json,re
VERSION='context-precision-evidence-control-v1'
INSTRUCTION='''Evaluate whether this retrieved context actually supplies evidence for at least one fact requested by the question, consistent with the reference answer. Partial but useful evidence is sufficient; the entire answer need not be present in one chunk.
The reference answer describes the target information. It is NOT evidence that the retrieved context contains that information. Never copy reference facts into the context or infer missing fees, amounts, deadlines, conditions, or requirements. A shared office or service name, or background about a different procedure, is not itself evidence for the requested facts.
Return exactly ONE JSON object with reason (string), verdict (the string "0" or "1"), and evidence_quotes (array of strings). For verdict "1", quote at least one short verbatim passage from this context that supports a requested fact. Preserve the context's numbers and words. Do not use ellipses or quotes from the reference instead. For verdict "0", use an empty evidence_quotes array. Stop after the object. Do not reproduce the prompt or examples.'''
def normalize_space(text):return re.sub(r'\s+',' ',text).strip()
def parse_grounded_verdict(raw,context):
    try:d=json.loads(raw)
    except (ValueError,TypeError):return None,'INVALID_JSON'
    if not isinstance(d,dict) or not isinstance(d.get('reason'),str) or d.get('verdict') not in ('0','1') or not isinstance(d.get('evidence_quotes'),list):return None,'INVALID_SCHEMA'
    quotes=d['evidence_quotes']
    if any(not isinstance(q,str) or not normalize_space(q) for q in quotes):return None,'INVALID_QUOTE_SCHEMA'
    if d['verdict']=='1' and not quotes:return None,'MISSING_POSITIVE_EVIDENCE'
    if d['verdict']=='0' and quotes:return None,'NEGATIVE_WITH_EVIDENCE_QUOTES'
    if any(normalize_space(q) not in normalize_space(context) for q in quotes):return None,'QUOTE_NOT_IN_CONTEXT'
    return d,None
