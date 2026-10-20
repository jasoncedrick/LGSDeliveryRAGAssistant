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
7. If the question is already English, copy it with only necessary grammar fixes.
   Preserve its service name, office, acronyms, action verbs, application stage,
   building height, quantities and conditions. Do not substitute a different office
   or replace receiving documents with submitting documents.
8. Write exactly one question on one line. Never continue the examples, generate
   a glossary, or introduce another Citizen Query. The glossary is input data.
   Retain acronyms supplied by the citizen even when expanding their meanings.

Examples:
Glossary:
- 'arkila': 'Contract of Lease for commercial business location'
Citizen Query: Asa ko magbayad sa arkila para sa akong pwesto?
Translated Query: Where do I pay the rent for my business location?

Glossary:
- 'sedula': 'Community Tax Certificate (CTC) issued by the City Treasurer'
Citizen Query: Tagpila ang kuha sa sedula kung walay trabaho?
Translated Query: How much is the fee for an individual Community Tax Certificate for unemployed individuals?
"""

BASELINE_SYSTEM_PROMPT = """You are a specialized query normalizer for Davao City's Electronic Business One-Stop Shop (eBOSS).
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



def translation_errors(raw_query, translated_query, response):
    """Check the translation contract; retain invalid output for offline review."""
    errors = []
    if not translated_query:
        errors.append('empty_translation')
    if '\n' in translated_query or re.search(
            r'\b(?:Glossary|Citizen Query|Translated Query)\s*:|```', translated_query, re.I):
        errors.append('extra_output')
    if (response.get('done') is False or response.get('done_reason') == 'length'
            or response.get('eval_count', 0) >= MAX_TRANSLATION_TOKENS):
        errors.append('incomplete_translation')
    for acronym in set(re.findall(r'\b[A-Z][A-Z0-9]{1,}\b', raw_query)):
        if not re.search(r'\b'+re.escape(acronym)+r'\b', translated_query, re.I):
            errors.append('missing_acronym:'+acronym)
    return errors

class QueryNormalizer:
    def __init__(self, dictionary_path: str = "data/municipal_dictionary_v1.json", *,
                 ollama_api_url: str = OLLAMA_API_URL, model_name: str = MODEL_NAME,
                 context_rules_path: str = None, enable_context_rules: bool = True,
                 enable_fidelity_contract: bool = False):
        self.enable_fidelity_contract = enable_fidelity_contract
        self.ollama_api_url = ollama_api_url
        self.model_name = model_name
        rule_path = context_rules_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config", "normalization_context_rules_v2.json")
        self.context_rules = {}
        # Legacy experiments retain their setting; the Chapter 3 web runtime
        # explicitly disables contextual sense guessing before ambiguity fallback.
        if enable_context_rules and os.path.exists(rule_path):
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

        system_prompt = FEW_SHOT_SYSTEM_PROMPT if self.enable_fidelity_contract else BASELINE_SYSTEM_PROMPT
        output_label = ("Translated Query (one question only; preserve supplied service and office):"
                        if self.enable_fidelity_contract else "Translated Query:")
        prompt = f"""{system_prompt}

Glossary:
{glossary_context}
Citizen Query: {raw_query}
{output_label}"""

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
            if not isinstance(result, dict) or result.get('error'):
                raise ValueError('Invalid normalization service response')
            translated_query = result.get("response", "").strip()
            raw_model_output = translated_query
            
            # Post-processing cleanup to ensure clean query string
            translated_query = re.sub(r'^(Translated Query:|Output:)\s*', '', translated_query, flags=re.IGNORECASE)
            translated_query = translated_query.strip('"\n ')

            errors = translation_errors(raw_query, translated_query, result) if self.enable_fidelity_contract else []
            diagnostics = {"raw_model_output": raw_model_output,
                           "done": result.get("done"), "done_reason": result.get("done_reason"),
                           "validation_errors": errors}
            if errors:
                return {"status": "ERROR", "normalized_query": None,
                        "clarification_prompt": None,
                        "injected_terms": [e["local_term"] for e in matched_entries],
                        "resolved_terms": scan_results["resolved_terms"],
                        "diagnostics": diagnostics, "tokens_generated": result.get("eval_count", 0)}

            return {
                "status": "SUCCESS",
                "term_id": None,
                "clarification_prompt": None,
                "normalized_query": translated_query,
                "diagnostics": diagnostics,
                "injected_terms": [e["local_term"] for e in matched_entries],
                "resolved_terms": scan_results["resolved_terms"],
                "tokens_generated": result.get("eval_count", 0),
                "eval_duration_ms": result.get("eval_duration", 0) / 1e6
            }

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to communicate with local Ollama server: {e}")

