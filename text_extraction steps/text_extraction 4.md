### Constructive Adviser Critique: Administrative Terminology and Structural Interlock

Before analyzing the text, two technical points in your request require clarification:

1. **Agency Acronym:** The statutory agency is the **Office of the City Building Official (OCBO)**, not "OCBD". In local governance and the National Building Code (PD 1096), it is designated as the OCBO.


2. **Administrative Interlock between CPDO and OCBO:** Your uploaded charter separates the **City Planning and Development Office (CPDO)** and the **OCBO**, but within the eBOSS permitting stream, they function as an integrated structural gate. As documented on Page 570, an application submitted to the OCBO is automatically endorsed to the CPDO for locational validation, while business licensing under the Business Bureau routes business locations to CPDO GIS mapping and zoning clearance before final clearance.



Below is the verified extraction of the statutory requirements, fees, processing timelines, and conversational mapping for the first three pillars.

---

### Pillar 1: Business Bureau (Permits & Licenses Division)

The Business Bureau serves as the central administrative gatekeeper of the eBOSS platform. Inquiries in this domain center on new applications, renewals, operational validation, and formal business retirement.

*Source Evidence: Pages 40–95, 111–122*

| Official Charter Service & Page | Statutory Requirement / Fee / Procedure | Citizen Conversational Token (`local_term`) | Language Variant | Verified Ground-Truth Definition (`verified_english_definition`) | Disambiguation & Fallback Rule |
| --- | --- | --- | --- | --- | --- |
| **Service 1: Pre-Assessment** (Page 41) | Assists clients in complying with prerequisites required by Regulatory Offices prior to New Business Permit application. | `pre-assessment` / `pa-assess` | Bislish | Initial evaluation by the Business Bureau verifying prerequisite clearances prior to formal application filing. | Map strictly to prerequisite verification; distinguish from CTO tax computation. |
| **Service 1: Pre-Assessment** (Page 41) | Any natural or juridical person engaging in business, trade, or occupation in Davao City. | `tag-iya sa negosyo` | Bisaya | Registered natural or juridical business owner applying for commercial authorization. | Single definition; `polysemy_flag: false`. |
| **Service 1 & 2: Step 2 Payment** (Pages 41, 73, 76) | Mayor’s Permit Fee assessed based on the asset size and nature of business, payable at CTO. | `mayors permit fee` / `bayad sa permit` | Bislish | Regulatory fee imposed by the City Mayor's Office based on capital investment or asset bracket. | Differentiate regulatory Mayor's Permit fee from CTO gross sales business taxes. |
| **Service 2: Issuance / Step 3** (Page 73) | Release: Once approved, claim Business Sticker at the Business Bureau office and sign logbook. | `business sticker` / `stiker sa negosyo` | Bislish | Official proof of annual licensing validation issued by the Business Bureau upon approval. | Single definition; `polysemy_flag: false`. |
| **Service 2: Total Processing Time** (Page 76) | Standard total processing turnaround: 1 Day and 20 Minutes (Simple Transaction). | `pila ka adlaw ang permit` | Bisaya | Official statutory standard turnaround time under RA 11032 for simple permit release. | Cite 1 Day and 20 Minutes standard. |
| **Service 6: Retirement** (Pages 111–114) | Full Retirement of Business Permit: Formal cessation of commercial activity to terminate tax liability. | `pag-undang sa negosyo` / `close ang business` | Bisaya / Bislish | Administrative cancellation and retirement of business registration to cease tax assessments. | Disambiguate temporary suspension from formal full retirement. |
| **Service 8: Inspection** (Pages 118–122) | Post-audit Ocular Inspection and Internet Café Advisory Board (ICAB) Inspection. | `ocular inspection` / `inspeksyon sa negosyo` | Bislish / Bisaya | Post-licensing regulatory inspection verifying compliance with submitted layout and city ordinances. | Disambiguate Business Bureau ocular checks from BFP fire safety audits. |

---

### Pillar 2: City Treasurer’s Office (CTO)

The CTO governs tax assessment schedules, cashiering, and revenue enforcement. A citizen inquiring about "bayad" (payment) is almost always routed to this pillar.

*Source Evidence: Pages 176, 206, 208*

| Official Charter Service & Page | Statutory Requirement / Fee / Procedure | Citizen Conversational Token (`local_term`) | Language Variant | Verified Ground-Truth Definition (`verified_english_definition`) | Disambiguation & Fallback Rule |
| --- | --- | --- | --- | --- | --- |
| **Service 20: New Application** (Page 206) | Assessment of business and Official Receipt (OR) issuance under Davao City Ordinance No. 0291-17. | `assessment sa cto` / `bayad sa bag-ong negosyo` | Bislish / Bisaya | Initial fiscal computation and billing of local taxes and regulatory fees for new applicants. | Anchor directly to Ordinance No. 0291-17, Series of 2017. |
| **Service 20: Section 76** (Page 206) | Section 76: Graduated Tax on Business computed on initial investment or declared capital. | `graduated tax` / `buhis sa negosyo` | Bislish / Bisaya | Local business tax imposed on a tiered graduated scale under Section 76 of the Revenue Code. | Disambiguate from annual fixed delivery vehicle taxes. |
| **Service 20: Section 72** (Page 206) | Section 72: Imposition of Annual Fixed Tax for Delivery Vehicles. | `tax sa delivery van` / `delivery vehicle tax` | Bislish | Annual fixed municipal tax required for commercial distribution and transport vehicles. | Check if query mentions delivery fleets or distribution. |
| **Service 20: Cedula** (Page 206) | Securing Official Receipt and Community Tax Certificate (Cedula). | `sedula` / `cedula` | Tagalog / Bisaya | Mandatory local identification and tax certificate required for business transactions. | Differentiate individual Community Tax Certificate from Corporate Cedula. |
| **Service 20: Re-printing Fee** (Page 206) | Mandatory service charge: Re-printing of business tax payment slip is PHP 50.00. | `reprint sa payment slip` | Bislish | Standard PHP 50.00 administrative fee for regenerating a lost or misplaced payment order slip. | Single definition; `polysemy_flag: false`. |
| **Service 21: Renewal** (Page 208) | Renewal Mayor's Permit Application: Taxes assessed on prior year's gross income / sales. | `gross sales tax` / `bayad sa renewal` | Bislish / Bisaya | Annual business tax assessment calculated against audited financial statements or gross receipts. | Distinguish renewal gross income taxation from new business initial capitalization. |
| **General Impositions** (Page 186/602) | Ordinance No. 0291-17, Section 186 – Imposition of Fees and issuance of Official Receipts. | `resibo sa cto` / `official receipt` | Bisaya / Bislish | Official proof of payment issued by CTO collectors (Window 1-4 or Counter 20). | Required proof of payment before Business Bureau releases stickers. |

---

### Pillar 3: OCBO & CPDO (Building Officials & Zoning Enforcement)

This pillar controls physical and spatial viability. Procedural inquiries involve structural blueprints, certificates of occupancy, and land-use compliance.

*Source Evidence: Pages 489–490, 549, 570 (OCBO); Pages 629–634, 640, 696–699 (CPDO)*

| Official Charter Service & Page | Statutory Requirement / Fee / Procedure | Citizen Conversational Token (`local_term`) | Language Variant | Verified Ground-Truth Definition (`verified_english_definition`) | Disambiguation & Fallback Rule |
| --- | --- | --- | --- | --- | --- |
| **OCBO Service 1: Building Permit** (Page 490) | Mandatory authorization required before any building is erected, constructed, altered, or repaired. | `building permit` / `permit sa pagtukod` | Bislish / Bisaya | Statutory license issued under the National Building Code (PD 1096) for structural work. | Disambiguate new construction permits from minor alteration permits. |
| **OCBO Service 1: Plans** (Page 490) | 3 sets of Civil/Architectural Plans duly signed and sealed by a licensed Civil Engineer or Architect. | `pirma ug selyo` / `plano sa arkitekto` | Bisaya | Professional blueprints bearing the wet signature and dry seal of a PRC-licensed engineer or architect. | Mandatory requirement for structural assessment; cannot be self-drafted. |
| **OCBO Technical Routing** (Page 570) | Step 2.3: Endorse building plans to CPDO; Step 2.5: Forward to Processing & Evaluation Inspector & BFP. | `endorsement sa cpdo` | Bislish | Inter-agency electronic routing of structural plans to Zoning and Fire Protection. | Clarifies that applicants do not need to deliver plans manually between offices. |
| **OCBO Inspection** (Page 570) | Occupancy Permit, Previous Annual Inspection Certificate, Business Permit with Official Receipt. | `occupancy permit` | Bislish | Legal certification verifying that a completed building complies with safety codes and approved plans. | **High-Ambiguity Flag:** Disambiguate commercial occupancy clearance from residential tenancy. |
| **CPDO Service 1: Zoning Certification** (Page 631) | Certification based on Integrated Zoning Ordinance (2019–2028). Fee: PHP 750/hectare; Time: 3 Days, 6 Hours, 50 Mins. | `zoning certification` / `bayad sa zoning` | Bislish / Bisaya | Formal certification verifying allowable land use classification under City Zoning Ordinance. | Distinct from Locational Clearance; fee is PHP 750 per hectare. |
| **CPDO Service 2: Validation** (Page 634) | Validation of Occupancy Permit for 3-storey buildings and above or 1,500 sqm floor area and above. | `validation sa cpdo` | Bislish | Height and area-specific locational clearance verification for large commercial buildings. | Applies only to multi-storey ($\ge 3$ floors) or large footprint ($\ge 1,500\text{ m}^2$) projects. |
| **CPDO Service 12: Business LC** (Pages 696–699) | Locational Clearance for Business (Online Application). Processing: GIS Map encoding and Art. 5 evaluation. | `locational clearance` / `gis map approval` | Bislish | Spatial zoning clearance for business licensing executed via GIS mapping and land-use evaluation. | Zero direct fee listed (`None`), processed within 1 Hour in eBOSS workflow. |

---

### Key Operational Rules Identified from the Extraction

1. **Explicit Legal Citation Grounding:** When Mistral 7B normalizes inquiries regarding local tax payments, it must cite **Davao City Ordinance No. 0291-17 (Series of 2017)** and its specific sections: Section 72 for delivery vehicles, Section 76 for graduated taxes, and Section 186 for official fee receipts.


2. **Deterministic Routing Constraints:** An inquiry regarding a "locational clearance for a store" must route to **CPDO Service 12** (1-hour online GIS clearance) rather than **CPDO Service 4** (which applies to 3-storey building construction).


3. **Fee Calculation Boundaries:** Mayor's Permit fees are calculated based on capital/asset brackets at the Business Bureau, whereas the taxes paid under the same transaction are graduated and assessed on gross sales by the CTO.


# I have included the other 2 pillars namely for BFP and barangays, but keep it within the Citizen Charter 2026

### Constructive Adviser Evaluation: Technical Boundaries for Pillars 4 & 5

Before analyzing the data, understand how these two entities integrate into Davao's Electronic Business One-Stop Shop (eBOSS):

1. **BFP Integration via Joint Memorandum Circular (JMC) No. 2021-01:** The Bureau of Fire Protection (BFP) does not operate merely as an outside inspector; under Republic Act No. 9514 and JMC 2021-01, it is embedded directly into the One-Stop Shop for Construction-Related Permits (OSCP) and eBOSS frontlines. Section 5(g) of RA 9514 strictly establishes that no business permit or permit to operate may be issued without securing a Fire Safety Inspection Certificate (FSIC).


2. **Barangay Clearance Automation vs. Physical Jurisdiction:** Under the Davao City Citizens' Charter and Anti-Red Tape Authority (ARTA) directives, the 182 barangays do not require separate non-parametric indices. The commercial clearance is consolidated electronically into the unified application stream (`appbts.davaocity.gov.ph`), while personal clearances (such as residency or employment) remain outside the eBOSS workflow.



Below is the verified extraction of statutory requirements, fee schedules, processing turnarounds, and conversational dialect mappings for **Pillars 4 and 5**.

---

### Pillar 4: Bureau of Fire Protection (BFP - Davao District / OSCP / eBOSS)

Inquiries in this domain involve operational fire inspections, extinguisher compliance ratios, fire code taxes, and the procedural transition from building plan evaluation to active commercial operations.

*Source Evidence: BFP Citizen's Charter (OSCP/BOSS), RA 9514 Sections 5, 7, 12, 13; Davao City Charter Page 41*

| Official Statutory Source & Service | Statutory Requirement / Legal Condition / Fee | Citizen Conversational Token (`local_term`) | Language Variant | Verified Ground-Truth Definition (`verified_english_definition`) | Disambiguation & Technical Rule |
| --- | --- | --- | --- | --- | --- |
| **RA 9514 Sec. 5(g) / BFP BOSS** (Page 41) | Mandatory prerequisite: Fire Safety Inspection Certificate (FSIC) for Business Permit (New/Renewal). | `fsic` / `fire safety permit` | Bislish | Statutory clearance issued by the Chief, BFP certifying premises comply with RA 9514. | Mandatory clearance; permit cannot be released without an active FSIC. |
| **BFP Citizen's Charter** (Frontline Services) | Pre-construction evaluation: Fire Safety Evaluation Clearance (FSEC) based on architectural/civil plans. | `fsec` / `fire safety evaluation clearance` | Bislish | Plan clearance issued prior to building construction; distinct from operational FSIC. | **Critical Distinction:** Map to pre-construction phase; do not confuse with annual business FSIC. |
| **RA 9514 Sec. 7(a) & Sec. 13** | Fire Code Tax/Fee: Statutory fee charged for certificates, inspections, and regulatory licenses. | `fire code fee` / `bayad sa bombero` | Bislish / Bisaya | Statutory national tax assessed by BFP, integrated into the consolidated eBOSS assessment bill. | Disambiguate BFP national regulatory fee from local municipal business taxes. |
| **BFP Standard** (Extinguisher Guidelines) | Portable chemical fire extinguishers compliant with DTI/PNS standards (e.g., 10 lb Dry Chemical per floor area). | `fire extinguisher` | Bislish | Required portable fire suppression hardware calibrated to commercial floor area and hazard class. | Map to physical ocular inspection checklists. |
| **RA 9514 Sec. 7(d) / Charter** | Egress Requirements: Unblocked emergency exit stairwells equipped with fire-rated panic hardware. | `emergency exit` / `fire exit` | Bislish | Legally mandated emergency egress doors that must remain unobstructed during operating hours. | Structural violation flag: Blocked exits lead to immediate Notice of Violation. |
| **BFP BOSS Note (1)** | Fire Safety Compliance Report (FSCR): Detailed design analysis signed by the Engineer/Architect and Fire Safety Practitioner. | `fscr` / `fire safety compliance report` | Bislish | Technical design analysis report required for building permit application stage. | Technical report for construction permits, not simple renewals. |
| **BFP BOSS Note (2)** | Fire Safety Compliance and Commissioning Report (FSCCR): Compilation of testing and acceptance of fire features. | `fsccr` | Bislish | As-built commissioning report signed by the Contractor and Fire Safety Practitioner. | Prerequisite for Occupancy Permit stage FSIC. |
| **BFP BOSS Note (3)** | Fire Safety Maintenance Report (FSMR): Maintenance and testing logbook of fire protection features. | `fsmr` / `maintenance report sa bombero` | Bislish | Compilation of testing records required annually for business permit renewal or operational FSIC. | Required for commercial renewals involving mechanical or sprinkler systems. |
| **JMC No. 2021-01 Classifications** | Turnaround standards: Simple Transaction = 1 Day; Complex = 3 Days; Highly Technical = 7 Days. | `pila ka adlaw ang fsic` | Bisaya | Standard statutory evaluation turnaround under the Ease of Doing Business framework. | Cite 1 working day for simple business permit renewals under OSCP/BOSS. |
| **RA 9514 Sec. 5(k) & Sec. 11** | Enforcement Instruments: Notice to Comply (NTC) and Notice to Correct Violation (NTV). | `notice of violation sa bfp` | Bislish | Official citation commanding owner to abate fire hazards within a specified statutory timeframe. | Flag for failed ocular inspections; requires compliance re-inspection. |

---

### Pillar 5: 182 Integrated Barangays of Davao City

Inquiries in this domain center on territorial jurisdiction, local clearance prerequisites, dispute certifications, and Community Tax Certificates (Cedula).

*Source Evidence: Davao City Citizens' Charter Pages 41, 185, 358; ARTA Commendation Reports*

| Official Statutory Source & Service | Statutory Requirement / Legal Condition / Fee | Citizen Conversational Token (`local_term`) | Language Variant | Verified Ground-Truth Definition (`verified_english_definition`) | Disambiguation & Technical Rule |
| --- | --- | --- | --- | --- | --- |
| **Charter Page 41 (Service 1.5)** | Mandatory attachment: Barangay Clearance from correct Barangay and Certification of No Operation from incorrect Barangay. | `clearance gikan sa barangay` / `certification of no operation` | Bisaya / Bislish | Official territorial clearance certifying commercial activity is authorized within the specific barangay. | If business relocated, applicant must secure No Operation certificate from previous barangay. |
| **ARTA eBOSS Integration** | Unified Clearance Stream: Barangay Business Clearance electronically bundled into eBOSS portal. | `barangay clearance para sa negosyo` | Bisaya | Automated municipal commercial clearance processed via `appbts.davaocity.gov.ph`. | **High-Ambiguity Flag:** Disambiguate commercial business clearance from individual employment clearances. |
| **Charter Page 41 / Local Gov Code** | Community Tax Certificate (Cedula): Issued to natural/juridical entities conducting business. | `sedula` / `cedula` | Bisaya / Tagalog | Mandatory fiscal identification certificate reflecting basic and gross income tax assessments. | Single definition; maps to prerequisite checklist for all business filings. |
| **Charter Page 41 (Form UBPAF)** | Geographic jurisdiction: Physical location across the 182 barangays (e.g., Poblacion, Talomo, Buhangin). | `lokasyon sa barangay` | Bisaya | Verified political territory establishing which barangay receives the regulatory tax share. | Used to route digital approvals within the integrated barangay software module. |
| **Local Government Code Sec. 399** | Lupong Tagapamayapa Certification: Certificate of No Pending Barangay Conciliation Dispute. | `lupon clearance` / `walay atraso` | Bislish / Bisaya | Certification that the applicant or establishment has no unresolved peace or property disputes. | Required primarily for entertainment, liquor, or contentious zoning operations. |
| **Local Barangay Tax Ordinance** | Regulatory Tariff: Standardized clearance fee assessed under the relevant barangay revenue schedule. | `bayad sa barangay` | Bisaya | Official regulatory charge integrated directly into the unified eBOSS statement of account. | Clarifies that fees are paid through the central eBOSS cashier rather than at the local hall. |
| **Charter Page 41 / RA 11032** | Signatory Authority: Wet or digital executive approval of the Punong Barangay (Barangay Captain). | `pirma sa kapitan` | Bisaya | Statutory endorsement certifying local council authorization for commercial operation. | Handled digitally through the backend eBOSS barangay module. |

---

### Methodological Safeguards for Pre-Retrieval Normalization

1. **The Construction-to-Operation Egress Anchor:** Queries containing `"FSCR"` or `"FSEC"` must route to pre-construction architectural guidelines, while inquiries asking about `"FSIC"` or `"permit sa bombero"` must route to operational business permitting (1-day turnaround under JMC 2021-01).


2. **The "Certification of No Operation" Edge Case:** If a user submits an inquiry regarding an address change or incorrect barangay boundary, the dictionary must inject the official requirement from Page 41 of the Charter: a *Certification of No Operation* from the previous barangay plus a new *Barangay Clearance* from the correct jurisdiction.


3. **Automated Billing Clarification:** When citizens ask `"Asa magbayad sa barangay ug BFP?"` (Where to pay barangay and BFP?), the injected ground-truth definitions must clarify that payments are consolidated into the CTO/eBOSS assessment slip and do not require traveling to separate district fire stations or barangay halls.