CURRENT CHECKPOINT

T06 harness: implemented and development validated.
T07 development: grid, A/B/C generation, scoring and matched-query comparison complete with documented limitations.
Full manuscript T07: NOT COMPLETE; registered freeze and final held-out A/B/C evaluation pending.

Read experiments/t06-t07-development-closeout-v1/READ_THIS_FIRST.txt
Completion evidence: completion_assessment.json
Matched results: matched_query_comparison.csv
Supplemental evaluator retries: judge_failure_review.json
Manual judge disagreement: manual_judge_check.json

All three faithfulness failures recovered with evaluator-only schema retries. Original runs and raw traces preserved and hashes verified. No original answer, context or reference replaced. Six clarification cases and one B incomplete generation retained.

No local model job from this closeout remains running. Held-out data untouched and app defaults unchanged.
Suggested branch checkpoint: thesis/t06-t07-development-reviewed-20261019
Branch not created automatically; no commit or push performed.


LATEST DEVELOPMENT REGRESSION: experiments/normalization-sparse-development-regression-v1/REVIEW_RESULTS.txt
All 90 queries tested per condition; no candidate promoted or frozen. New-ranked contexts need Context Precision evaluation before selection.


PUNCTUATION CANDIDATE CONTEXT PRECISION GRID RUNNING
Read experiments/punctuation-context-precision-v1/METHOD_ALIGNMENT.txt
17 weights x K3/K5, unchanged 90 development queries. Archived normalization retained; rejected prompt not used.
Monitor: Get-Content D:\thesis\LGSDeliveryRAGAssistant-clean\experiments\punctuation-context-precision-v1\console.log -Tail 15 -Wait
Future launch/resume command, after existing judge finishes: D:\thesis\venv\Scripts\python.exe -B scripts/run_punctuation_context_precision.py
No promotion or freeze.


LATEST OBJECTIVE REVIEW
experiments/punctuation-context-precision-v1/REVIEW_RESULTS.txt
INCOMPLETE_JUDGING_REQUIRES_FAILURE_REVIEW
No deployment or freeze.

SUPPLEMENTAL FORMAT RECOVERY REVIEW: experiments/punctuation-context-precision-format-retry-v2/REVIEW_RESULTS.txt
No deployment or freeze.


EVIDENCE COVERAGE REVIEW
experiments/bfp002-evidence-coverage-review-v1/READ_THIS_FIRST.txt
HOLD promotion and freeze. Calibrate the offline evaluator before interpreting the small objective improvement. Original scores are preserved.


OFFLINE JUDGE CALIBRATION FINISHED
Read experiments/context-precision-calibration-v1/REVIEW_DECISION.txt
Original judge: 27/30 negative controls accepted. Evidence candidate: 57/60 invalid outputs. Neither evaluator is validated for promotion.
T06 runner implemented; judge reliability unresolved. Full T07 is pending. Original results remain unchanged.


T06 IMPLEMENTATION CLOSED
experiments/t06-harness-closeout-v2/T06_STATUS.txt
Complete against tracker batch-harness deliverable, with explicit evaluator limitations. This does not close T07 final evaluation.
V2 opt-in real batch integration passed; old evaluator and original scores preserved.


T07 UPDATE: Paired original/punctuation grid rescore is running with evaluator v2. See experiments/t07-paired-grid-evaluator-v2/READ_THIS_FIRST.txt and progress.json. T06 implementation remains complete; final T07 is pending. No freeze or held-out access.


PAIRED RESCORE REVIEW: 1560/1560 attempted; 1450 valid, 110 invalid after the registered retry. All 68 conditions have nulls; no final selection. See experiments/t07-paired-grid-results-review-v1/READ_THIS_FIRST.txt. No scoring process is active from this review. T06 implementation remains complete; T07 pending.


STRUCTURED FORMAT TEST COMPLETE: 60 controls, 58 valid, 57 correct, one false positive and two quote failures. Screening rule not met; no full grid started. See experiments/context-precision-calibration-v3-structured/REVIEW_DECISION.txt. No calibration process remains active. T07 still pending.


T06 FINAL IMPLEMENTATION CLOSEOUT V3: 34 focused tests passed. T06 coding deliverable complete with evaluator limitations. Source-span calibration finished: 60 valid, 46 correct, 14 false positives; candidate rejected and conditional stress test not run. No scoring process active. See experiments/t06-harness-closeout-v3/T06_STATUS.txt. T07 remains pending; no freeze or held-out access.
