"""Website adapter: explicit dictionary-option selection and private diagnostics.

Never infers a sense from prior chat. A user must include an option verbatim.
The base dictionary, translation prompt and settings remain unchanged.
"""
import copy
import re


class WebsiteNormalizer:
    def __init__(self, base):
        self.base=base
        self.last_trace=None

    def normalize(self, query):
        current=copy.copy(self.base)
        current.dictionary=dict(self.base.dictionary)
        selected=[]
        for term,entry in self.base.dictionary.items():
            if not entry.get('polysemy_flag') or not re.search(r'\b'+re.escape(term)+r'\b',query,re.I):
                continue
            options=re.findall(r'\[Option [A-Z]:\s*(.*?)\]',entry.get('disambiguation_rule',''))
            explicit=[option for option in options if option.casefold() in query.casefold()]
            if len(explicit)==1:
                current.dictionary[term]={**entry,'polysemy_flag':False,'verified_english_definition':explicit[0]}
                selected.append({'term_id':entry['term_id'],'explicit_option':explicit[0]})
        result=current.normalize(query)
        self.last_trace={**result,'explicit_user_selections':selected}
        return result
