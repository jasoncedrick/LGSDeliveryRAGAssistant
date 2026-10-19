RESEARCH CHECKPOINT - FINAL EVALUATION IN PROGRESS
Captured: 2026-10-19T21:18:25.713048+08:00
Branch: thesis/t07-evaluation-checkpoint-20261019
Parent: 633fbfda282bc41432078c076fde22f7ebcdafbb

This checkpoint contains completed development evidence, implementation,
tests, mock rater materials and the employee annotation meeting packet.
T06 implementation and the 270-interaction DEVELOPMENT A/B/C comparison
are complete with the limitations recorded in their reports.

Final held-out A/B/C evaluation was running at capture: 70 groups,
210 queries per architecture, 630 planned generation outcomes.
This commit does not contain or claim completed held-out results.
The separate final-run registration and execution manifest are included.

Excluded from this checkpoint: active final interaction files and metrics,
final RAGAS outputs, live status folder, logs, process locks, temporary
files and PRIVATE_ review-key files. Held-out benchmark questions and
answers are not added. Referenced local-only files may therefore be absent.

Methodology references: 20260923.pdf Chapter 3 and the archived authoritative
Thesis Tracker evidence. Known implementation differences and limitations
remain: 17 weight combinations rather than the manuscript's 0.1 grid;
answer-format guidance does not fully implement its two-example description;
legacy judge semantic errors; static lexical guidance retained in C;
source-span transfer complete for 59/70 groups, with missing Hit/MRR explicit.
The crosswalk addendum was registered after structural preflight and before
model outcomes. Do not describe registration as full methodology certification.

Current development results:
experiments/t07-methodology-reconciliation-v1/READ_THIS_FIRST.txt
experiments/t07-methodology-reconciliation-v1/master_metrics.csv
Final-run protocol:
experiments/t07-final-evaluation-v1/EXECUTION_GUIDE.txt

The running working branch, real Git staging index, source files, frozen
inputs and running processes were left unchanged when this commit was made.
This is a publication snapshot, not an instruction to relaunch a live run.
