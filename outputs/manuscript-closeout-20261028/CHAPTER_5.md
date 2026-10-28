# Chapter 5 Conclusions Limitations and Recommendations

## 5.1 Summary of the study

This study implemented and evaluated a dictionary-assisted hybrid retrieval-augmented generation assistant for code-switched local government service inquiries in Davao City. Its workflow combines charter-based preprocessing, municipal terminology assistance, constrained query normalization, chunk-level retrieval and local answer generation. Evaluation compared a raw-query BM25 baseline, the proposed pipeline and an injection-disabled ablation. Automated execution covered 70 held-out scenario groups in three language variants, while the amended expert audit examined a category-balanced subset of 20 groups through separate normalization and answer modules.

The completed implementation and evaluation address the research objectives, but the results do not support an unqualified claim that the proposed system is superior. The hybrid configurations improved descriptive retrieval on the original complete-label subset. Expert ratings showed strong ordinal agreement, yet paired comparisons did not establish significant differences among the tested systems. The distinction between implementation, retrieval success and final answer quality is central to interpreting the study.

## 5.2 Conclusions by research objective

### 5.2.1 Capturing charter identifiers and conversational intent

The study demonstrates an implementable architecture for connecting multilingual citizen inquiries to source-linked charter passages without supervised model fine-tuning. Actual-token windows, page provenance and preserved extraction repairs make the evidence used by generation inspectable. Dictionary assistance and constrained normalization provide a mechanism for handling local terminology before lexical and dense retrieval. The registered runtime preserves a reproducible division between preprocessing, retrieval, generation and offline evaluation.

Implementation does not guarantee semantic fidelity. The expert normalization medians were 4 on the five-point scale, but lower-rated outputs remained. Meaning, service, actor direction and explicit qualifiers must therefore be evaluated rather than assumed to survive translation. Ambiguity clarification and retrieval failure should remain distinct: a query may be clear even when the returned evidence is inadequate, and a fluent translation may still change its intent.

### 5.2.2 Comparing the proposed architecture with baselines

The proposed pipeline had higher descriptive Hit@3 and MRR@3 than raw-query BM25 on the original 177-query complete-label subset. This supports a limited conclusion that the combined normalization and hybrid retrieval workflow found relevant annotated material more effectively in those observations. The later 210-query reconciled label export is reported separately because it extends the original source-label coverage.

The incremental benefit of query-specific dictionary injection was not established. B and C had identical Hit@3 on the original subset and close MRR@3, normalization and answer relevance values. C retained shared static lexical guidance, so this ablation does not represent the total absence of linguistic knowledge. The paired human tests did not demonstrate significant B-C differences. The study consequently cannot claim that dictionary injection alone caused the observed retrieval advantage over A.

### 5.2.3 Evaluating relevance and factual faithfulness

The study produced both automated and human evidence of answer quality. Ordinal agreement coefficients exceeded .80 for all three human dimensions, indicating consistent ratings on the supplied assessments. At the same time, answer relevance means were approximately 2.3 on the four-point scale and faithfulness means ranged from approximately 2.6 to 2.7. These results identify limitations in procedural completeness and factual precision rather than establishing uniformly reliable service guidance.

No primary human comparison reached statistical significance after the seven-test Holm correction. The appropriate conclusion is that this audit did not establish superior human-rated performance of the proposed configuration. It does not demonstrate equivalence or rule out a difference in a larger, independently planned sample. High rater agreement and high system performance are separate properties and should not be conflated.

## 5.3 Limitations

The source collection is limited to the studied charter documents and service categories. It does not represent every government service, policy revision or transactional workflow. Source ambiguities and repaired table layouts remain relevant to interpretation. Retrieval-label transfer follows source spans across changed chunk boundaries and can include small boundary overlaps; later reconciliations extend coverage but do not retroactively make all labels part of the original registration.

The generator and offline evaluator used the local Mistral family, and the judge has documented output-format and semantic errors. Missing judge scores were retained and reported. Matched metric denominators differ, so automated means do not represent complete observations for all 210 queries on every measure. The human audit uses only 20 groups and three fixed raters, with exploratory rather than prospectively registered comparison tests.

The audit sample was selected after automated outcomes. The selection rule did not use performance scores, but the timing still limits a claim of preselection. Blinding is also imperfect because content and shared output-ID suffixes can reveal cross-module relationships. The independent-scoring attribution relies on the researcher's explicit confirmation and preserves the earlier conflicting metadata. No statistical coefficient substitutes for collection documentation.

The study did not measure citizen satisfaction, completion time, staff workload, cost savings, legal compliance or actual permit outcomes. Claims that the assistant reduces office congestion, eliminates misleading advice or improves service delivery in practice would exceed the available evidence. Existing app defaults were not automatically synchronized to the evaluated configuration, so operational demonstrations require a configuration check.

## 5.4 Recommendations

### 5.4.1 Maintain the municipal dictionary as a versioned resource

The current dictionary should remain a static, versioned component for reproducing the completed study. Each future term revision should retain its source, service scope, governance tags, ambiguity information and review history. Additions should distinguish legitimate alternative senses from incorrect mappings. A new dictionary version should be tested on development data and evaluated under a new declared protocol; the known held-out failures should not be used to silently improve and re-report the frozen test run.

The present results do not justify expanding the dictionary indiscriminately or claiming that every injected definition improves normalization. Future ablations should separate query-specific injection from shared static prompt guidance and measure intent preservation directly. A more discriminating study could preregister service, actor, direction, quantity and condition errors as separate analysis categories while retaining a clear overall fidelity judgment.

### 5.4.2 Strengthen source representation and evidence coverage

Future source ingestion should continue checking table wording, row relationships, quantities, units, conditions and page references against rendered charters. Uncertain printed values should be preserved and explicitly identified rather than corrected by guesswork. New corpora and indices should be versioned together, with coverage and chunk/index alignment checks retained.

Retrieval and generation errors should be analyzed separately. Wrong-service passages, incomplete context and intent-changing normalization require different interventions. Any new method that carries additional service context must be tested within a prospectively specified development study. It should not be introduced into the already evaluated pipeline and described as the method that produced the archived results.

### 5.4.3 Plan a stronger follow-up evaluation

A follow-up study should register the audit sample, scoring instructions, no-claim policy, primary comparisons and analysis methods before inspecting final outcomes. Separate module identifiers should prevent direct cross-module output linkage, and collection records should distinguish independent scores from facilitated discussion or later adjudication. Additional scenario groups should be justified by a prospective precision or power analysis rather than selected until a favorable p-value appears.

Evaluator validation should use evidence-linked checks and preserve failed scoring attempts. Agreement should be reported with uncertainty and with clear limitations on generalization beyond the observed raters. If the intended claim is practical equivalence, the study should define an acceptable difference margin in advance and use an appropriate equivalence design rather than interpreting a nonsignificant difference as equality.

### 5.4.4 Keep deployment claims proportional to evidence

Any operational pilot should identify the exact corpus, dictionary, retriever and model versions in use and provide traceable citations for procedural answers. Staff escalation should remain available when the source is ambiguous or the retrieved evidence is insufficient. A separate authorized pilot would be needed to measure citizen outcomes and staff workload. The prototype should not be represented as an official transaction system or a replacement for authoritative city guidance.

## 5.5 Final conclusion

The study provides a reproducible implementation and a documented comparison of dictionary-assisted hybrid RAG for multilingual charter inquiries. The hybrid configurations showed descriptive retrieval gains over the lexical baseline on the original evaluable subset, while the expert audit found consistent ratings without statistically established system superiority. The contribution is the implemented workflow, source-linked evidence archive and measured account of its benefits and limitations. Further claims about dictionary-specific benefit, universal factual reliability or real-world service improvement require additional prospective evidence.
