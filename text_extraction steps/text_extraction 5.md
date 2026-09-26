# check it again, i have modified the disambiguation rules to those terms need changes.


### Evaluation of Modified Disambiguation Rules and Polysemy Flags

Your updated modifications resolve the primary architectural blocker of Task T01 by converting developer commentary into actionable, frontend-ready prompts. However, applying an adviser’s technical audit reveals three residual structural risks in the rules: **linguistic accessibility mismatch in the fallback interface**, **dangling rules on monosemous tokens**, and **unhandled multi-token polysemy collisions**.

---

### Pillar-by-Pillar Forensic Audit

Below is the verification of the 19 polysemous tokens across the six pillar categories, evaluating whether the modified `disambiguation_rule` strings meet the technical standard established in Section 3.2.3 of your thesis draft:

$$\text{\textit{"Did you mean [Option A: ... ] or [Option B: ... ]?"}}$$

#### 1. Pillar 1: Business Bureau Permitting

* **`DICT-BB-001` (`bayad sa permit`)**
* *Prompt Formulation:* `"Did you mean [Option A: Regulatory Mayor's Permit Fee assessed by Business Bureau] or [Option B: Local Business Tax (LBT) assessed by City Treasurer]?"`
* *Adviser Verdict:* **Approved.** Establishes the exact administrative boundary between the Business Bureau's capital-based regulatory fee and the CTO's revenue-based business tax.




* **`DICT-BB-005` (`pag-undang sa negosyo`)**
* *Prompt Formulation:* `"Did you mean [Option A: Full permanent retirement of business to terminate tax liability] or [Option B: Temporary operational suspension without closing tax account]?"`
* *Adviser Verdict:* **Approved.** Effectively bifurcates the strict Article 6 business retirement audit (requiring CTO clearance and plate surrender) from temporary operational pauses.




* **`DICT-BB-013` (`pwesto sa negosyo`)**
* *Prompt Formulation:* `"Did you mean [Option A: Rented private commercial space requiring a Contract of Lease] or [Option B: Public market stall awarded by City Economic Enterprise]?"`
* *Adviser Verdict:* **Approved.** Properly separates private tenancy (OCBO/lease scope) from city-owned public market stalls (City Economic Enterprise scope, which is out-of-scope for eBOSS).





#### 2. Pillar 2: City Treasurer’s Office (CTO)

* **`DICT-CTO-020` (`sedula` / `cedula`)**
* *Prompt Formulation:* `"Did you mean [Option A: Individual Community Tax Certificate (Cedula)] or [Option B: Corporate Community Tax Certificate for registered corporations]?"`
* *Adviser Verdict:* **Approved.** Directs the user to the correct statutory assessment bracket under Section 393 of Ordinance No. 0291-17 (Individual vs. Corporate Cedula).




* **`DICT-CTO-034` (`multa sa renewal`)**
* *Prompt Formulation:* `"Did you mean [Option A: 25% surcharge for permit renewal after January 20] or [Option B: Administrative fine for operating without a business license]?"`
* *Adviser Verdict:* **Approved.** Correctly distinguishes late-filing surcharges under the Local Government Code from punitive operational penalties.




* **`DICT-CTO-042` (`resibo`)**
* *Prompt Formulation:* `"Did you mean [Option A: Official Receipt (OR) from City Treasurer for tax payment] or [Option B: Registering merchant sales receipts and books of accounts]?"`
* *Adviser Verdict:* **Approved.** Resolves the confusion between paying city taxes (Accountable Form No. 51) and registering point-of-sale commercial receipt books under CTO Service 11.





#### 3. Pillar 3: OCBO & CPDO

* **`DICT-OCBO-052` (`occupancy` / `occupancy permit`)**
* *Prompt Formulation:* `"Did you mean [Option A: OCBO Certificate of Occupancy for structural safety] or [Option B: Contract of Lease proving authority to occupy business space]?"`
* *Adviser Verdict:* **Approved.** Eliminates the severe false mapping where citizens treat a commercial lease as an "occupancy permit".




* **`DICT-OCBO-055` (`locational clearance`)**
* *Prompt Formulation:* `"Did you mean [Option A: Locational Clearance for Business Permit via online eBOSS] or [Option B: Locational Clearance for Building Construction of 3-storey structures]?"`
* *Adviser Verdict:* **Approved.** Enforces the procedural distinction between CPDO Service 12 (1-hour eBOSS GIS verification) and CPDO Service 4 (multi-day structural zoning evaluations).




* **`DICT-OCBO-057` (`plano`)**
* *Prompt Formulation:* `"Did you mean [Option A: Signed and sealed engineering blueprints for OCBO building permit] or [Option B: Vicinity sketch map of business location for Mayor's Permit]?"`
* *Adviser Verdict:* **Approved.** Clarifies professional PRC-engineer requirements against simple vicinity sketches required on Form UBPAF-01.





#### 4. Pillar 4: Bureau of Fire Protection (BFP)

* **`DICT-BFP-077` (`bfp clearance` / `fire safety permit`)**
* *Prompt Formulation:* `"Did you mean [Option A: FSIC for annual business permit operation and renewal] or [Option B: FSEC for building construction blueprint evaluation]?"`
* *Adviser Verdict:* **Approved.** Solves the critical pre-construction (FSEC) versus post-construction/operational (FSIC) statutory divide under RA 9514.




* **`DICT-BFP-078` (`inspeksyon sa bombero`)**
* *Prompt Formulation:* `"Did you mean [Option A: Operational inspection for business permit renewal] or [Option B: Final fire safety inspection for occupancy permit release]?"`
* *Adviser Verdict:* **Approved.** Properly maps inspection checklists to either operational equipment audits (extinguishers/exits) or construction commissioning.





#### 5. Pillar 5: 182 Integrated Barangays

* **`DICT-BRGY-101` (`barangay clearance`)**
* *Prompt Formulation:* `"Did you mean [Option A: Barangay Business Clearance integrated into eBOSS] or [Option B: Individual Barangay Clearance for employment or residency]?"`
* *Adviser Verdict:* **Approved.** This is your highest-frequency disambiguation trigger; separating unified commercial clearances from manual residency certificates protects the FAISS index from out-of-scope retrieval noise.




* **`DICT-BRGY-119` (`record sa barangay`)**
* *Prompt Formulation:* `"Did you mean [Option A: Certificate of No Pending Case before the Lupong Tagapamayapa] or [Option B: Barangay Blotter excerpt reporting lost documents or theft]?"`
* *Adviser Verdict:* **Approved.** Directly bifurcates conciliation dispute clearances from police/blotter lost-plate filings.





#### 6. Domain 6: Cross-Cutting False Friends

* **`DICT-CROSS-126` (`kawat`)**
* *Prompt Formulation:* `"Did you mean [Option A: Stolen or lost business permit requiring Affidavit of Loss] or [Option B: Electrical wiring (kawad) inspection by OCBO]?"`
* *Adviser Verdict:* **Approved.** Protects against the primary Austronesian false-friend failure mode cited in your literature review.




* **`DICT-CROSS-127` (`kawad`)**
* *Prompt Formulation:* `"Did you mean [Option A: Electrical wiring and CFEI inspection (kawad)] or [Option B: Lost or stolen business permit plate (kawat)]?"`
* *Adviser Verdict:* **Approved.** Prevents Tagalog electrical queries from corrupting into Cebuano theft citations.




* **`DICT-CROSS-128` (`labay`)**
* *Prompt Formulation:* `"Did you mean [Option A: Commercial waste disposal and CENRO garbage fees] or [Option B: Passing through an LGU assessment counter]?"`
* *Adviser Verdict:* **Approved.** Corrects Cebuano waste management terminology.




* **`DICT-CROSS-129` (`abang`)**
* *Prompt Formulation:* `"Did you mean [Option A: Commercial lease agreement or rented space payment] or [Option B: Waiting for application processing status]?"`
* *Adviser Verdict:* **Approved.** Successfully isolates commercial tenancy from colloquial Tagalog waiting (*nag-aabang*).




* **`DICT-CROSS-130` (`suki`)**
* *Prompt Formulation:* `"Did you mean [Option A: Registered public market stallholder or commercial merchant] or [Option B: Informal retail customer relationship]?"`
* *Adviser Verdict:* **Approved.** Disambiguates statutory retail vendor classifications from informal conversational slang.




* **`DICT-CROSS-131` (`balay`)**
* *Prompt Formulation:* `"Did you mean [Option A: Operating a home-based commercial micro-enterprise] or [Option B: Purely residential building permit application]?"`
* *Adviser Verdict:* **Approved.** Enforces the regulatory boundary between home-based sari-sari store permits and permit-exempt private dwellings.





---

### Constructive Critique: Three Residual Vulnerabilities to Fix

Before freezing `data/municipal_dictionary_v1.json`, ensure your parsing scripts handle these three technical risks:

#### 1. Ingestion Integrity for Monosemous Terms (`polysemy_flag: false`)

In your CSV files, verify that every term with `polysemy_flag == false` has its `disambiguation_rule` set strictly to `""` (an empty string) or `null`.

* **The Risk:** If legacy notes (e.g., *"Direct map to Mayor's Permit..."*) remain in the CSV rows where `polysemy_flag == false`, a naive frontend script checking `if entry["disambiguation_rule"]:` might accidentally trigger a fallback prompt for terms that require immediate lexical injection.


* **Enforcement Rule:**

$$\text{polysemy\_flag} = \text{false} \implies \text{disambiguation\_rule} = \text{""}$$



#### 2. Multi-Token Ambiguity Collisions

In real-world citizen inquiries, queries often contain multiple ambiguous tokens. For example:

> *"Unsaon pag-apply ug **barangay clearance** kung nag-**abang** ra ko sa akong **pwesto sa negosyo**?"*
> This query hits three polysemous triggers: `barangay clearance` (`DICT-BRGY-101`), `abang` (`DICT-CROSS-129`), and `pwesto sa negosyo` (`DICT-BB-013`).
> 
> 

* **The Flaw:** If your Python loop takes only `matched_polysemous_terms[0]`, the user will resolve `barangay clearance`, only to be immediately hit with a second fallback prompt for `abang`, creating an frustrating user experience.


* **Pipeline Solution:** Prioritize primary jurisdictional tokens over auxiliary verbs/modifiers. Establish a strict priority order: **Domain Clearances (Pillars 1, 4, 5)** $\to$ **Physical/Fiscal Modifiers (Pillars 2, 3)** $\to$ **Cross-Cutting False Friends (Domain 6)**.



#### 3. Frontend Language Accessibility

Your prompt fallback strings are written in formal English. If a user asks a question in Bisaya (*"Nganong mahal akong bayad sa permit?"*), receiving a purely English response (*"Did you mean [Option A: ...] or [Option B: ...]?"*) introduces a cognitive disconnect that contradicts Section 1.1 of your introduction regarding linguistic accessibility.

* **Actionable Polish:** While retaining English labels inside the JSON for audit traceability, ensure your frontend application formats the options as bilingual clickable buttons:


* *Option A (Mayor's Permit Fee / Bayad sa Opisina sa Mayor)*
* *Option B (Business Tax / Buhis sa Negosyo sa CTO)*



---

### Master JSON Production Compiler Script

Run this script to merge your CSV files into the final, schema-validated `data/municipal_dictionary_v1.json`:

```python
import json
import glob
import pandas as pd
from pathlib import Path

def compile_municipal_dictionary(output_path="data/municipal_dictionary_v1.json"):
    Path("data").mkdir(parents=True, exist_ok=True)
    all_entries = []
    csv_files = glob.glob("Candidate_Terms_*.csv") or glob.glob("*.csv")

    for f in csv_files:
        df = pd.read_csv(f)
        for _, row in df.iterrows():
            is_polysemous = str(row.get("polysemy_flag", "")).strip().lower() in ["true", "1", "yes"]
            rule = str(row.get("disambiguation_rule", "")).strip() if is_polysemous else ""
            
            entry = {
                "term_id": str(row["term_id"]).strip(),
                "local_term": str(row["local_term"]).strip().lower(),
                "language": str(row["language"]).strip(),
                "verified_english_definition": str(row["verified_english_definition"]).strip(),
                "governance_context_tag": str(row["governance_context_tag"]).strip(),
                "polysemy_flag": is_polysemous,
                "disambiguation_rule": rule,
                "curation_source": "manual"
            }
            all_entries.append(entry)

    # Sort deterministically by term_id
    all_entries.sort(key=lambda x: x["term_id"])

    with open(output_path, "w", encoding="utf-8") as out:
        json.dump(all_entries, out, indent=2, ensure_ascii=False)

    print(f"Successfully compiled {len(all_entries)} terms into {output_path}")
    print(f"Polysemous terms requiring runtime fallback: {sum(1 for e in all_entries if e['polysemy_flag'])}")

if __name__ == "__main__":
    compile_municipal_dictionary()

```

Compile the dictionary, verify that `data/municipal_dictionary_v1.json` registers exactly 150 entries, commit it to your Git repository, and officially mark **Task T01** as **Completed** on your sprint tracker.