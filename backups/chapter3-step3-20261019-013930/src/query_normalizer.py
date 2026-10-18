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
5. Preserve the citizen's question type, timing trigger and scope. A deadline for
   the citizen to submit/register is different from an agency's processing duration.
   Do not replace one with the other. Preserve late-registration versus late-filing
   distinctions and any explicit event such as filing an application.
6. Do not add an answer, time limit, amount, qualification or premise that the
   citizen did not supply. Glossary definitions resolve vocabulary only.

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
    def __init__(self, dictionary_path: str = "data/municipal_dictionary_v1.json", *,
                 ollama_api_url: str = OLLAMA_API_URL, model_name: str = MODEL_NAME,
                 context_rules_path: str = None):
        self.ollama_api_url = ollama_api_url
        self.model_name = model_name
        rule_path = context_rules_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config", "normalization_context_rules_v2.json")
        self.context_rules = {}
        if os.path.exists(rule_path):
            with open(rule_path, encoding="utf-8") as handle:
                rules = json.load(handle)
            if rules.get("schema_version") != 1 or not isinstance(rules.get("terms"), dict):
                raise ValueError("Invalid contextual normalization rules")
            for term_id, senses in rules["terms"].items():
                if not isinstance(senses, list) or not senses:
                    raise ValueError("Sense list cannot be empty")
                for sense in senses:
                    if not sense.get("sense_id") or not sense.get("english_definition"):
                        raise ValueError("Sense identity/definition is required")
                    groups = sense.get("required_any_groups")
                    if not isinstance(groups, list) or not groups or any(not g for g in groups):
                        raise ValueError("Each sense needs nonempty evidence groups")
                    for group in groups:
                        for pattern in group:
                            if not isinstance(pattern, str) or not pattern:
                                raise ValueError("Invalid evidence pattern")
                            re.compile(pattern)
            self.context_rules = rules["terms"]
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
        resolved_terms = []

        for term in self.sorted_terms:
            pattern = rf"\b{re.escape(term)}\b"
            if re.search(pattern, raw_query, flags=re.IGNORECASE):
                entry = dict(self.dictionary[term])
                if entry.get("polysemy_flag", False):
                    matches = []
                    for sense in self.context_rules.get(entry.get("term_id"), []):
                        evidence = []
                        for group in sense["required_any_groups"]:
                            found = [m.group(0) for pattern in group
                                     if (m := re.search(pattern, raw_query, re.I))]
                            if not found:
                                break
                            evidence.append(found[0])
                        else:
                            matches.append((sense, evidence))
                    if len(matches) == 1:
                        sense, evidence = matches[0]
                        entry["verified_english_definition"] = sense["english_definition"]
                        resolved_terms.append({"term_id": entry.get("term_id"),
                            "local_term": term, "sense_id": sense["sense_id"],
                            "evidence": evidence})
                    else:
                        polysemous_triggers.append(entry)
                matched_entries.append(entry)

        return {
            "matched_entries": matched_entries,
            "polysemous_triggers": polysemous_triggers,
            "resolved_terms": resolved_terms
        }

    def normalize(self, raw_query: str) -> Dict[str, Any]:
        """
        Executes the three-stage normalization pipeline:
        1. Sub-module 4.3: Ambiguity Fallback verification
        2. Sub-module 4.1: Lexical Injection context construction
        3. Sub-module 4.2: Constrained Mistral 7B translation
        """
        scan_results = self.scan_query(raw_query)
        poly_conflicts = scan_results["polysemous_triggers"]
        matched_entries = scan_results["matched_entries"]

        # Sub-module 4.3: Ambiguity Fallback Mechanism
        if poly_conflicts:
            priority_conflict = poly_conflicts[0]
            clarification = priority_conflict.get(
                "disambiguation_rule",
                f"Did you mean {priority_conflict.get('local_term')} for business licensing or another procedure?"
            )
            return {
                "status": "FALLBACK_TRIGGERED",
                "term_id": priority_conflict.get("term_id", ""),
                "clarification_prompt": clarification,
                "normalized_query": None,
                "injected_terms": [e["local_term"] for e in matched_entries],
                "resolved_terms": scan_results["resolved_terms"],
                "tokens_generated": 0,
                "eval_duration_ms": 0.0
            }

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
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "top_p": 0.0,
                "num_predict": MAX_TRANSLATION_TOKENS
            }
        }

        try:
            response = requests.post(self.ollama_api_url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            translated_query = result.get("response", "").strip()
            
            # Post-processing cleanup to ensure clean query string
            translated_query = re.sub(r'^(Translated Query:|Output:)\s*', '', translated_query, flags=re.IGNORECASE)
            translated_query = translated_query.strip('"\n ')

            return {
                "status": "SUCCESS",
                "term_id": None,
                "clarification_prompt": None,
                "normalized_query": translated_query,
                "injected_terms": [e["local_term"] for e in matched_entries],
                "resolved_terms": scan_results["resolved_terms"],
                "tokens_generated": result.get("eval_count", 0),
                "eval_duration_ms": result.get("eval_duration", 0) / 1e6
            }

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to communicate with local Ollama server: {e}")

