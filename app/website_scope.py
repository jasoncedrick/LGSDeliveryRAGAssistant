"""Conservative pre-generation coverage checks, not a faithfulness evaluator.

Post-study website addition. This never reranks, substitutes or expands passages.
A pass does not establish entailment; a miss intentionally favors abstention.
"""
import re

OFFICES = {
    'CPDO': ('cpdo', 'city planning'), 'OCBO': ('ocbo', 'ocbd'),
    'BFP': ('bfp',), 'CTO': ('city treasurer',),
}
TOPICS = [
    (r"\b(?:business permit|mayor'?s? permit|mayoral permit)\b", r'\bbusiness permit\b'),
    (r'\bbuilding permit\b|\bbuild\w*\b.{0,25}\bhouse\b', r'\bbuilding permit\b'),
    (r'\boccupancy permit\b', r'\boccupancy\b'),
    (r'\b(?:cedula|sedula|community tax)\b', r'\b(?:community tax|cedula|ctc)\b'),
    (r'\b(?:weld\w*|hot.work)\b', r'\b(?:weld\w*|hot.work)\b'),
    (r'\bneighbou?rs?\b|\bsilingan\b|\bkapitbahay\b', r'\bneighbou?rs?\b'),
]


def coverage_issue(query, citations):
    texts=[' '.join(c.get('text','').lower().split()) for c in citations]
    joined='\n'.join(texts)
    relevant=texts
    for office, filenames in OFFICES.items():
        if re.search(r'\b'+office+r'\b',query,re.I) and not any(
            any(name in c.get('file_source','').lower() for name in filenames) for c in citations):
            return 'requested_office_absent:'+office
    for requested, required in TOPICS:
        if re.search(requested,query,re.I):
            matching=[text for text in texts if re.search(required,text,re.I)]
            if not matching:
                return 'requested_topic_absent'
            relevant=matching
    if re.search(r'\blocational clearance\b',query,re.I) and re.search(r'\b(?:business|negosyo)\b',query,re.I):
        if not re.search(r'locational clearance.{0,85}business|business.{0,85}locational clearance',joined,re.I):
            return 'requested_business_clearance_scope_absent'
    # Asking what happens first requires evidence of order, not just a form name.
    if re.search(r'\b(?:what|which)\b.{0,65}\bfirst\b',query,re.I) and not re.search(
        r'\b(?:before|prior|first|after)\b|\b1[.)]\s','\n'.join(relevant)):
        return 'requested_sequence_absent'
    if re.search(r'what document|what.{0,35}bring|which document|unsa.{0,30}requirements',query,re.I):
        if not re.search(r'checklist|requirement|document|\bform\b|photocop|original|\bcopy\b|w-2|2316|tax declaration','\n'.join(relevant)):
            return 'requested_checklist_evidence_absent'
    return None
