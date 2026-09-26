import os
import re
import json
import requests
from typing import Dict, Any, List

OLLAMA_API_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "eboss-mistral"
MAX_TRANSLATION_TOKENS = 150  # Hard ceiling mandated by Section 3.2.3

# Standard few-shot template adhering to Sub-module 4.2
FEW_SHOT_SYSTEM_PROMPT = """You are a specialized query normalizer for Davao City's Electronic Business One-Stop Shop (eBOSS).
Your sole task is to translate citizen inquiries submitted in Bisaya, Tagalog, Bislish, or Taglish into concise, formal English governance search queries matching the Davao City Citizens' Charter.

Rules:
1. Output ONLY the translated English search query.
2. Do NOT answer the question.
3. Do NOT add pleasantries, explanations, preamble, or quotation marks.
4. Utilize the provided glossary definitions to replace localized administrative slang with official Citizens' Charter terminology.

Examples:
Glossary:
- 'arkila': 'Contract of Lease for commercial business location'
Citizen Query: Asa ko magbayad sa arkila para sa akong pwesto?
Translated Query: Where do I submit the Contract of Lease for my business location?

Glossary:
- 'sedula': 'Community Tax Certificate (CTC) issued by the City Treasurer'
Citizen Query: Tagpila ang kuha sa sedula kung walay trabaho?
Translated Query: How much is the fee for an individual Community Tax Certificate for unemployed individuals?
"""

class QueryNormalizer:
    def __init__(self, dictionary_path: str = "data/municipal_dictionary_v1.json"):
        if not os.path.isabs(dictionary_path) and not os.path.exists(dictionary_path):
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            dictionary_path = os.path.join(project_root, dictionary_path)
        if not os.path.exists(dictionary_path):
            raise FileNotFoundError(f"Dictionary file not found at: {dictionary_path}")
            
        with open(dictionary_path, "r", encoding="utf-8") as f:
            self.dictionary: Dict[str, Dict[str, Any]] = json.load(f)

        # FIX: compiledictionary.py stores the term as the JSON key only.
        # Copy it into each entry so e["local_term"] works below.
        for term, entry in self.dictionary.items():
            entry.setdefault("local_term", term)
            
        # Match longest multi-word phrases first to prevent partial substring collision
        self.sorted_terms = sorted(self.dictionary.keys(), key=len, reverse=True)

    def scan_query(self, raw_query: str) -> Dict[str, Any]:
        """
        Scans inquiry using regex word boundaries (\b) to isolate matched municipal terms
        and detect polysemy triggers.
        """
        matched_entries = []
        polysemous_triggers = []

        for term in self.sorted_terms:
            pattern = rf"\b{re.escape(term)}\b"
            if re.search(pattern, raw_query, flags=re.IGNORECASE):
                entry = self.dictionary[term]
                matched_entries.append(entry)
                if entry.get("polysemy_flag", False):
                    polysemous_triggers.append(entry)

        return {
            "matched_entries": matched_entries,
            "polysemous_triggers": polysemous_triggers
        }

    def normalize(self, raw_query: str) -> Dict[str, Any]:
        """
        Executes the three-stage normalization pipeline:
        1. Sub-module 4.3: Ambiguity Fallback verification (flag only, no longer skips translation)
        2. Sub-module 4.1: Lexical Injection context construction
        3. Sub-module 4.2: Constrained Mistral 7B translation
        """
        scan_results = self.scan_query(raw_query)
        poly_conflicts = scan_results["polysemous_triggers"]
        matched_entries = scan_results["matched_entries"]

        # Sub-module 4.3: Ambiguity Fallback Mechanism
        #
        # FIX: previously this returned immediately with normalized_query=None,
        # forcing every downstream consumer (including the T07 eval harness) to
        # fall back to the RAW, untranslated citizen query whenever a polysemous
        # term was detected. That silently tanked retrieval metrics on ~11% of
        # non-English test queries and had nothing to do with whether dictionary
        # injection helps -- it was just the system giving up on translation
        # entirely. A live chatbot should still ask the user to disambiguate, but
        # it should ALSO hand back a best-effort translated search query so
        # retrieval isn't left searching with raw Bislish/Taglish text. So: keep
        # flagging the ambiguity (status + clarification_prompt), but no longer
        # skip the translation step below.
        clarification_prompt = None
        flagged_term_id = ""
        status = "SUCCESS"
        if poly_conflicts:
            priority_conflict = poly_conflicts[0]
            clarification_prompt = priority_conflict.get(
                "disambiguation_rule",
                f"Did you mean {priority_conflict.get('local_term')} for business licensing or another procedure?"
            )
            flagged_term_id = priority_conflict.get("term_id", "")
            status = "FALLBACK_TRIGGERED"

        # Sub-module 4.1: Dictionary-Assisted Lexical Injection
        injected_definitions = [
            f"- '{e['local_term']}': '{e['verified_english_definition']}'"
            for e in matched_entries
        ]
        glossary_context = "\n".join(injected_definitions) if injected_definitions else "None"

        prompt = f"""{FEW_SHOT_SYSTEM_PROMPT}

Glossary:
{glossary_context}
Citizen Query: {raw_query}
Translated Query:"""

        # Sub-module 4.2: Constrained LLM Query Translation via Ollama API
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "top_p": 0.0,
                "num_predict": MAX_TRANSLATION_TOKENS
            }
        }

        try:
            response = requests.post(OLLAMA_API_URL, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            translated_query = result.get("response", "").strip()
            
            # Post-processing cleanup to ensure clean query string
            translated_query = re.sub(r'^(Translated Query:|Output:)\s*', '', translated_query, flags=re.IGNORECASE)
            translated_query = translated_query.strip('"\n ')

            return {
                "status": status,
                "term_id": flagged_term_id or None,
                "clarification_prompt": clarification_prompt,
                "normalized_query": translated_query,
                "injected_terms": [e["local_term"] for e in matched_entries],
                "tokens_generated": result.get("eval_count", 0),
                "eval_duration_ms": result.get("eval_duration", 0) / 1e6
            }

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to communicate with local Ollama server: {e}")
        