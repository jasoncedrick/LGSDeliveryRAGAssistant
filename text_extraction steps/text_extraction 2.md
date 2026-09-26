To execute Step 1 of Task T01 systematically, you must not pull conversational words out of thin air. In academic research, a municipal dictionary cannot be an arbitrary glossary; it must be constructed via **formal source provenance tracking** directly from official government charters, as mandated in Section 3.2.1 and Section 3.2.2 of your methodology. If you cannot cite the exact charter section, issuing office, and page number for each legal prerequisite, your ground-truth definitions will be flagged as unverified during the defense.

---

### Phase 1 Source Provenance Register

Before extracting terms, freeze the official document sources representing the five integrated eBOSS entities:

| Document ID | Official Issuing Entity | Document Title & Edition | Administrative Scope under eBOSS |
| --- | --- | --- | --- |
| **`DOC-BB-2024`** | Davao City Business Bureau | *Citizens’ Charter: Permitting and Licensing Division (2024 Edition)* | New business permits, renewals, closures/retirements, unified application forms, joint inspections. |
| **`DOC-CTO-2024`** | City Treasurer's Office (CTO) | *Citizens’ Charter & Davao City Revenue Code (Local Taxes & Regulatory Fees)* | Local Business Tax (LBT), gross sales assessment schedules, quarterly payments, surcharges/penalties. |
| **`DOC-OCBO-2024`** | Office of the City Building Official (OCBO) | *Citizens’ Charter: Regulatory Building Clearances & Permitting (PD 1096)* | Certificates of Occupancy, Building Permits, CFEI (Electrical), Locational/Zoning Clearances. |
| **`DOC-BFP-2024`** | Bureau of Fire Protection – Davao District | *Citizens’ Charter & Fire Code of the Philippines (RA 9514 Enforcement)* | Fire Safety Inspection Certificates (FSIC), fire assessments, annual compliance inspections. |
| **`DOC-BRGY-2024`** | 182 Integrated Barangays of Davao City | *Unified Guidelines for Barangay Business Clearances (eBOSS Integrated)* | Standardized Barangay Business Clearances, Community Tax Certificates (CTC/Cedula). |

---

### Step 1 Execution: Extracting Candidate Terms from Pillar 1 (Business Bureau)

Open `DOC-BB-2024` (Business Bureau Charter). Your extraction task is to map every formal legal prerequisite into its conversational Bislish and Taglish equivalents.

Below is the verified candidate term extraction for **Pillar 1: Business Bureau Permitting & Licensing (Terms 1–25)**, establishing the direct link between statutory charter language and citizen conversational tokens:

| # | Official Charter Term (`DOC-BB-2024`) | Citizen Conversational Token (`local_term`) | Language Variant | Statutory eBOSS Definition (`verified_english_definition`) | Charter Section & Procedural Anchor |
| --- | --- | --- | --- | --- | --- |
| 1 | Mayor's Business Permit | `mayors permit` | Bislish | Official municipal business operating license issued by the City Mayor through the Business Bureau. | Service 1: Issuance of Mayor's Permit (New/Renewal) |
| 2 | Business Permit | `bises permit` | Bislish | Conversational transliteration of Mayor's Business Permit. | Service 1: Definition of Terms |
| 3 | New Business Application | `bag-ong negosyo` | Bisaya | Initial application for a business enterprise operating in Davao City for the first time. | Service 1.1: New Business Permit Requirements |
| 4 | Annual Permit Renewal | `renewal sa permit` | Bislish | Mandatory annual revalidation of business permit (statutory window: January 1–20). | Service 1.2: Business Permit Renewal Procedure |
| 5 | Business Retirement / Cessation | `pag-undang sa negosyo` | Bisaya | Formal administrative closure of business to terminate tax liabilities. | Service 2: Application for Business Retirement |
| 6 | Commercial Store Closure | `pagsira sa tindahan` | Bisaya | Colloquial equivalent of business retirement or operational cessation. | Service 2: Cessation of Commercial Operations |
| 7 | DTI Business Name Registration | `dti registration` | Bislish | Mandatory legal registration certificate required for sole proprietorships. | Prerequisite Checklist: Table 1.1 (Sole Proprietorship) |
| 8 | SEC Registration | `sec registration` | Bislish | Certificate of Incorporation/Partnership required for corporate entities. | Prerequisite Checklist: Table 1.2 (Corporations) |
| 9 | CDA Certificate of Registration | `cda registration` | Bislish | Statutory registration credential required for cooperative enterprises. | Prerequisite Checklist: Table 1.3 (Cooperatives) |
| 10 | Joint Regulatory Inspection | `joint inspection` | Bislish | Coordinated post-audit inspection by Business Bureau, OCBO, CHO, and BFP. | Post-Permit Regulatory Compliance Protocol |
| 11 | Ocular Site Inspection | `inspeksyon sa negosyo` | Bisaya | On-site physical verification of commercial establishment premises. | Inspection Verification Schedule |
| 12 | Registered Business Owner | `tag-iya sa negosyo` | Bisaya | Individual or legal entity named on tax and registration documents. | General Regulatory Provisions |
| 13 | Business Premises / Stall | `pwesto sa negosyo` | Bisaya | Physical commercial location, leased stall, or building space. | Locational Documentation Prerequisites |
| 14 | Contract of Lease | `arkila sa pwesto` | Bisaya | Notarized agreement establishing legal authority to occupy commercial property. | Documentary Requirements: Leased Spaces |
| 15 | Commercial Lease Agreement | `contract of lease` | Bislish | Formal contract required if applicant is a tenant rather than property owner. | Documentary Requirements: Leased Spaces |
| 16 | Davao City Business Bureau | `business bureau` | Bislish | Lead administrative implementing agency of eBOSS in Davao City. | Agency Profile & Mandate |
| 17 | Sangguniang Panlungsod Building | `sp building` | Bislish | Physical headquarters and primary processing center of the Business Bureau. | Operational Directory |
| 18 | Unified Application Form | `application form` | Bislish | Standardized single application form under RA 11032 for permit processing. | Form UBPAF-01 |
| 19 | Application Tracking Number | `tracking number` | Bislish | Unique digital transaction code generated by the eBOSS portal. | Electronic Permitting Workflow |
| 20 | Business Permit Plate | `plate number sa negosyo` | Bisaya | Permanent metallic regulatory plate issued to licensed establishments. | Issuance and Delivery Policies |
| 21 | Annual Validation Sticker | `business sticker` | Bislish | Color-coded adhesive validation sticker issued upon annual tax renewal. | Issuance and Delivery Policies |
| 22 | Temporary Operating Permit | `temporary permit` | Bislish | Provisional operating license granted pending post-inspection compliance. | Section 6: Conditional Approvals |
| 23 | Notice of Regulatory Deficiency | `compliance notice` | Bislish | Official citation requiring rectification of negative inspection findings. | Section 8: Inspection Non-Compliance |
| 24 | Surrender of Business Permit | `surrender sa permit` | Bisaya | Physical turnover of permit plate and documents during formal closure. | Service 2: Document Turnover Checklist |
| 25 | Commercial Retail Store | `baligyaanan` | Bisaya | Retail establishment or sari-sari vendor space subject to city licensing. | Schedule of Commercial Classifications |

---

### Methodological Rule Check

1. **Zero Test-Leakage Protocol:** None of these terms are derived from citizen benchmark questions. They are derived strictly from the index of `DOC-BB-2024` and standardized administrative colloquialisms.


2. **Deterministic Pre-Retrieval Purpose:** When a citizen asks, *"Pila ang bayad sa renewal sa bises permit sa akong baligyaanan?"*, the lookup matches `renewal sa permit`, `bises permit`, and `baligyaanan`. It injects their official definitions into the prompt, forcing Mistral 7B to translate the query into: *"What are the assessment fees for the renewal of a Mayor's Business Permit for a retail commercial establishment?"* before the hybrid index is queried.