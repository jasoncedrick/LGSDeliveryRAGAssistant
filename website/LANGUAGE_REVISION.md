# Website response-language revision — 28 October 2026

The reported question was “ano need magpagawa ng building”; the website answered in English. The original pipeline passed the original question to generation and already requested language matching. That general instruction did not reliably control this model's output language.

Chapter 3, PDF page 31 (printed page 26) of `D:\thesis\20260923.pdf` explicitly describes response language matching. This website revision adds a specific language instruction to the generation call. It is a post-study implementation change, not a reproduction of the frozen T07 generation prompt. T07 metrics and expert ratings do not validate this new prompt.

## Exact behavior

- Previously: the original question and English source passages were passed with the general frozen answer prompt.
- Now: the same inputs are passed with the frozen prompt plus the separately versioned instruction in `config/website_response_language_v2.json`.
- Auto mode uses lexical clues in the original question to select English, Taglish or Bislish. It is a limited heuristic, not a validated language classifier. The citizen can override it with **Answer in**.
- The override changes only the generation instruction. It does not translate the retrieval query, alter the selected passages, or change normalization.
- The request-local instruction reuses the original generator implementation, including the complete-prompt budget check and fixed settings. There is one generation call, with no automatic translation, repair loop or live evaluator.
- The exact unsupported-answer fallback and structured ambiguity responses remain governed by the original protocol; they are exceptions to the new generated-explanation language setting. Error messages and interface labels are not fully localized.

The corpus, dictionary, reviewed normalization prompt, indices, 120/20 token windows, K=3 and fusion weights remain unchanged. The original website implementation is retained in Git commit `25b3d4f`; both language prompt candidates and their outputs are preserved.

## Evidence and limitations

`experiments/website-language-fidelity-v1/` retains the first candidate's three questions, answers and cited passages. It switched languages but produced awkward Taglish, invented acronym expansions and unsupported details. It was not promoted. Version 2 simplifies the language instruction and explicitly preserves technical terms and partial-source limitations. Its same three smoke questions are in `experiments/website-language-fidelity-v2/`.

These are targeted website checks using the reported question and two newly written variants. They are not a rerun of the development or held-out benchmark, a human language evaluation, or a factual-faithfulness certification. Language compliance does not establish correct service coverage or complete requirements. See the recorded review in the version 2 folder for observed outcomes.

API tests also cover request isolation, unchanged inputs/settings, citation handling, exact fallback, invalid language options and budget protection. Browser checks cover the selector's submitted value and desktop/mobile layout. No manuscript, tracker workbook, reference labels, frozen result or human rating is rewritten.
