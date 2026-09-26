To complete **Task T01 ("Draft Municipal Dictionary")**, you must understand its exact role in your thesis architecture: it is not a general glossary, but the primary deterministic safety net of your pre-retrieval normalization pipeline. It stabilizes code-switched Bisaya-English (Bislish) and Tagalog-English (Taglish) queries and prevents cross-lingual semantic corruption before text reaches the embedding model and vector database.

---

### 1. Architectural Scope and Boundaries

Your manual curation must strictly align with the approved **eBOSS regulatory ecosystem**:

* **Corpus Source Boundaries:** Extract terms exclusively from the official Citizens' Charters, local tax ordinances, and procedural checklists of the five integrated eBOSS entities: the **Business Bureau**, **City Treasurer’s Office (CTO)**, **Office of the City Building Official (OCBO)**, **Bureau of Fire Protection (BFP)**, and the **182 Integrated Barangays**.


* **Strict Exclusion of Out-of-Scope Offices:** Do not include terminology from the City Health Office (Health Certificates) or the City Civil Registrar (birth, marriage, death records). These departments operate outside the eBOSS digital licensing stream (appbts.davaocity.gov.ph).


* **Domain 6 (False Friends and Transliterations):** Systematically include conversational administrative transliterations (e.g., *bises permit*, *arkila*, *resibo*) and critical Cebuano-Tagalog false friends (e.g., Cebuano *kawat* [theft] vs. Tagalog *kawad* [wire]) to prevent severe translation and retrieval failures.



---

### 2. Standardized JSON Schema Contract

The final output of T01 must be saved to `data/municipal_dictionary_v1.json`. To satisfy the requirements of Chapter 3, every entry must include eight structured fields:

```json
{
  "term_id": "DICT-BB-001",
  "local_term": "bises permit",
  "language": "Bislish",
  "verified_english_definition": "Mayor's Business Permit issued by the Davao City Business Bureau",
  "governance_context_tag": "Business Bureau",
  "polysemy_flag": false,
  "disambiguation_rule": "Direct map to Mayor's Permit renewal or new application prerequisites.",
  "curation_source": "manual"
}

```

* **`term_id`**: A unique string identifier prefixed by domain (e.g., `DICT-BB-001`, `DICT-CROSS-126`).


* **`local_term`**: The lowercase conversational token or compound phrase as used in citizen inquiries.


* **`language`**: The source dialect/code-switch type (`Bisaya`, `Tagalog`, `Bislish`, or `Taglish`).


* **`verified_english_definition`**: The exact legal or procedural definition taken from the Citizens' Charter.


* **`governance_context_tag`**: One of the five eBOSS pillars or general procedural categories (`Business Bureau`, `Treasurer_Office`, `OCBO`, `BFP`, `Barangay`, or `Cross_Cutting`).


* **`polysemy_flag`**: A boolean (`true` / `false`) indicating if the term has multiple conflicting meanings across governance or colloquial contexts.


* **`disambiguation_rule`**: Explicit instruction for the translation prompt or ambiguity fallback handler detailing how to resolve conflicting definitions.


* **`curation_source`**: Hardcoded to `"manual"` for Layer 1.



---

### 3. Step-by-Step Execution Plan for T01

```
Step 1: Citizens' Charter Text Extraction (5 eBOSS Pillars)
                           │
                           ▼
Step 2: Candidate Term Identification (Target: ~150 Layer 1 Terms)
                           │
                           ▼
Step 3: False-Friend & Polysemy Audit (Tagalog vs. Cebuano Disambiguation)
                           │
                           ▼
Step 4: JSON Validation & Regex Boundary Check (O(1) Hashmap Lookup)
                           │
                           ▼
Step 5: Zero-Leakage Audit & Pipeline Freeze (Lock v1.0 before T05 benchmark)

```

1. **Collate Source Charters:** Open the official Davao City Citizens' Charter PDFs for the Business Bureau, CTO, OCBO, BFP, and Barangay Clearances.


2. **Curate the Target Allocation (150 Terms):**
* Business Bureau (New & Renewal Business Permits): ~25 terms.


* City Treasurer’s Office (Taxes, Fees, Assessments): ~25 terms.


* OCBO (Building, Occupancy, Electrical, Locational/Zoning Clearances): ~25 terms.


* Bureau of Fire Protection (FSIC, inspections, fire taxes): ~25 terms.


* 182 Integrated Barangays (Business Clearances, CTC/Cedula, Purok endorsements): ~25 terms.


* Cross-Cutting Procedures & Dialect False Friends: ~25 terms.




3. **Audit Polysemy and Ambiguity Triggers:**
* For every entry, evaluate whether the word has conflicting senses (e.g., *barangay clearance* for personal employment vs. commercial licensing; or *kawat* vs. *kawad*).


* Set `polysemy_flag: true` and write the exact prompt fallback question in `disambiguation_rule` (e.g., *"Did you mean [Option A: Stolen document] or [Option B: Electrical wiring]?"*).




4. **Format and Store:**
* Format the dataset into a key-indexed JSON hashmap to allow $O(1)$ lookup time in your Python preprocessing pipeline.


* Implement word-boundary regular expressions (`\b` + `re.escape(term)` + `\b`) to ensure naive substrings (e.g., matching *abang* inside *pagpabanga*) do not trigger false positive injections.




5. **Enforce the Zero-Leakage Protocol:**
* Under no circumstances may terms be derived from the 70 reserved held-out test scenario groups.


* All vocabulary must originate strictly from the Citizens' Charter texts, known conversational administrative patterns, or the 30 development question groups.




6. **Freeze and Commit:**
* Save the finalized dataset as `data/municipal_dictionary_v1.json`.


* Commit the file to your Git repository, log its cryptographic hash, and officially mark **T01** as **Completed** on your sprint tracker.