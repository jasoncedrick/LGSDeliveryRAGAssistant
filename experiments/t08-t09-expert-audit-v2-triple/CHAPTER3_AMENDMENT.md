# Proposed replacement: Section 3.2.9 expert audit allocation and instruments

This amendment records the researcher-supplied adviser mandate dated 26 October
2026. The original `20260923.pdf` and tracker remain unchanged source documents.
Their existing A/B-only allocation is superseded for the new human collection
by this documented amendment; it was not a requirement already in the PDF.

Three independent domain auditors evaluate two modules using the same registered,
category-balanced subset of 20 scenario groups, four per category. The subset
was selected after automated T07 evaluation and before human scoring using a
fixed hash ordering of group IDs, without selecting on performance. This timing
must be disclosed; it is not preselection before automated evaluation.

Module 1 evaluates pre-retrieval normalization from Configurations B and C for
40 code-switched queries: 20 Taglish and 20 Bislish. Each auditor rates both
archived outputs independently against the original query using the statement:
“This normalized query preserves the meaning, intent, and explicit details of
the original query.” The five-point agreement scale is 1 Strongly Disagree,
2 Disagree, 3 Neither Agree nor Disagree, 4 Agree and 5 Strongly Agree.
This yields 80 output-level ratings per auditor and 240 across three auditors.

Module 2 evaluates final generated responses from Configurations A, B and C
for all 60 queries (20 groups, three language variants). Each auditor reviews
180 responses, yielding 540 response-level records and 1,080 dimension scores
across three auditors when complete. Answer Relevance and Factual Faithfulness
retain the independent four-point ordinal rubrics in Table 2. The five-point
Module 1 agreement scale does not replace or modify Table 2.

Outputs and actual retrieved passages remain unedited. System names are masked
and order is randomized independently per auditor and module. For Module 2,
cyclic rotations balance each architecture across X/Y/Z positions, with each
architecture in each position 20 times per auditor and each query occupying all
three positions across the auditors. Module 1 balances B/C left and right
20 times per auditor. Separate opaque IDs and independently randomized module
orders reduce cross-module identity cues; content may still reveal similarities.
The custodian has the private mapping and is not blind. A blinded facilitator
must not access it. Perfect blinding is not claimed.

Collection uses five sessions: Module 1 followed by four Module 2 blocks of
15 queries. At least ten minutes of break are required between sessions and
after the first 20 Module 1 queries. Additional breaks are permitted. Duration
depends on evidence review; breaks do not guarantee a reliability threshold.

Final exports require ratings in the module's specified scale; unfinished drafts
may retain blanks. No ratings are imputed. Clarification or incomplete outputs
are evaluated as presented, with concerns recorded in notes. Experts consult
the facilitator about procedural uncertainty without receiving a prescribed score.

Report ordinal Krippendorff's alpha separately for Module 1 fidelity and for
each Module 2 dimension. Do not pool the five-point and four-point scales.
The manuscript's alpha >= .80 remains a target, not a guaranteed result or a
test of system superiority. Comparative analyses must respect paired queries,
scenario/language dependence and repeated raters. Retain missingness and
collection problems transparently. The 240 and 540 records are separate
datasets, not 780 independent scenarios.

## Tracker alignment (Thesis Tracker tab)

- T08: prepare 40 blinded normalization pairs and 60 blinded answer triples.
- T09: implement separate five-point fidelity and four-point answer instruments.
- T10: collect three independent sets; 240 Module 1 and 540 Module 2 records.
- T11: compute separate ordinal reliability estimates from real ratings.
- T12: perform declared paired analyses; do not invent or guarantee significance.

This file is replacement text for incorporation into the editable manuscript
and corresponding tracker descriptions. It does not claim those external files
have been edited. No frozen T06/T07 evaluation or source reference was changed.
