"""Format computed human-audit results and targeted tracker edits."""
from pathlib import Path
import json,html,hashlib,shutil
import openpyxl
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'experiments/t10-t12-human-analysis-v1'
d=json.loads((OUT/'analysis_results.json').read_text())
def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,r))+' |' for r in rows])+'\n'
report='''# Human expert audit: T10-T12 results

Analysis date: 28 October 2026. The six supplied assessments contain 780 output-review records and 1,320 dimension scores. All expected records, score ranges, packet identities, question/output text, presentation order and JSON/CSV score pairs passed validation. No scores were imputed, changed or excluded from the primary analysis.

The researcher explicitly confirmed independent scoring by three experts without exposure to AI-suggested scores and confirmed that these files contain their exact submitted scores. Earlier files carried conflicting AI-prepared metadata; the originals and the researcher's correction are preserved. Results below are conditional on that confirmed provenance. Statistical agreement alone cannot verify independent collection, auditor qualifications, or blinding.

## Table 1. Dataset coverage

| Module | Queries | Unique outputs | Reviewers | Review records | Dimension scores |
| --- | --- | --- | --- | --- | --- |
| M1: normalization (B/C) | 40 | 80 | 3 | 240 | 240 |
| M2: generated answers (A/B/C) | 60 | 180 | 3 | 540 | 1,080 |

Module 1 uses the approved 1-5 agreement statement for normalization fidelity. Module 2 retains the separate 1-4 Answer Relevance and Factual Faithfulness rubrics from Table 2. Each module uses the same registered 20 scenario groups, four from each service category. M1 contains Taglish and Bislish; M2 also contains English. Rater codes, not names, are used in analysis.

## Table 2. Ordinal inter-rater reliability

'''
report+=table(['Dimension','Unique outputs','Alpha','95% cluster-bootstrap CI','Meets .80 point target'],[(r['module']+' '+r['dimension'],r['unique_outputs'],f"{r['ordinal_alpha']:.4f}",f"[{r['ci95_low']:.4f}, {r['ci95_high']:.4f}]",'Yes' if r['point_meets_080'] else 'No') for r in d['reliability']])
report+='''
All three point estimates exceed .80. The percentile intervals also have lower bounds above .80, although faithfulness is close to the threshold (approximately .801). Intervals are based on 2,000 bootstrap draws of scenario groups within service categories; they are estimates, not guarantees. All raters, languages and configurations remain together within each sampled group. The three observed raters are treated as fixed. This agreement result does not establish factual correctness or system superiority.

## Table 3. Descriptive scores by configuration

'''
report+=table(['Dimension','Configuration','Ratings','Mean','Median'],[(r['module']+' '+r['dimension'],r['configuration'],r['rating_count'],f"{r['mean']:.4f}",f"{r['median']:.1f}") for r in d['descriptives'] if r['language']=='all'])
report+='''
Means summarize the numeric coding of the ordinal scales; score distributions and language breakdowns are supplied in descriptive_scores.csv. They should not be interpreted as calibrated interval measurements. B and C have very similar normalization and relevance means. B has the largest descriptive faithfulness mean, but the paired analysis does not establish superiority.

## Table 4. Scenario-paired comparisons

'''
report+=table(['Dimension','Contrast','Mean difference','95% descriptive CI','Exact p','Holm p'],[(r['module']+' '+r['dimension'],r['contrast'],f"{r['mean_difference']:.4f}",f"[{r['ci95_low']:.4f}, {r['ci95_high']:.4f}]",f"{r['p_value']:.6f}",f"{r['holm_p_value']:.4f}") for r in d['comparisons']])
report+='''
Each comparison uses 20 paired scenario groups. Within each scenario/configuration, ratings are averaged across the three raters and applicable languages (six M1 or nine M2 ratings). Exact two-sided signed-rank tests enumerate the sign distribution using midranks for ties and omit zero differences. The seven primary p-values receive one joint Holm adjustment. Confidence intervals are unadjusted descriptive group-bootstrap intervals; they are not simultaneous hypothesis tests. Rank-biserial effects, numbers of tied/nonzero groups, and two-sided group sign-test sensitivity p-values are in paired_comparisons.csv.

No comparison is significant at the .05 level after correction; all Holm-adjusted p-values equal 1.0000. This is absence of evidence for a difference in this audit, not proof that the systems are equivalent. In the B-C faithfulness comparison, only three of 20 groups have a nonzero difference; the rank-biserial value of 1 applies only to those three groups and must not be described as a universal or large practical advantage.

## Table 5. No-factual-claim sensitivity (descriptive only)

'''
report+=table(['Configuration','Outputs excluded in sensitivity','Primary faithfulness mean','Mean excluding flagged outputs'],[(r['configuration'],r['excluded_outputs'],f"{r['primary_mean']:.4f}",f"{r['without_no_claim_outputs_mean']:.4f}") for r in d['no_claim_sensitivity']])
report+='''
The primary results retain every submitted rating. This separate diagnostic excludes an output if any reviewer flagged it as containing no factual claims. It does not recode abstentions to 4 or replace the primary analysis. The historical files described a no-claim scoring convention not specified verbatim in Table 2; the methodological interpretation should be disclosed. This sensitivity uses unequal denominators and is not a new paired significance test.

## Methods, limitations and interpretation

- The plan was written before this computation but after ratings and prior summaries were available. The comparisons are exploratory, not retrospectively preregistered or confirmatory.
- Signed-rank inference assumes independent scenario groups and symmetric differences under the null. Averaging ordinal scores uses the chosen numeric coding. Group sign-test sensitivity does not require the difference-symmetry assumption; none of those sensitivity p-values is below .05.
- The audit subset was selected after automated T07 results, using fixed category-balanced hash ordering. The timing disclosure remains. Inference concerns this limited audit sample, not all municipal services or a random population of expert raters.
- Module 1 and Module 2 opaque output IDs share suffixes for 80 outputs. Cross-module matching was possible, and textual similarity can also reveal links. Do not claim perfect blinding. No packet IDs or issued materials were altered after collection.
- Researcher-confirmed independent scoring is used as the data provenance; earlier conflicting metadata and its correction remain inspectable. No collection timestamps, qualifications, signatures or direct observations are invented.
- The original manuscript states an A/B-only human allocation. The adviser-directed 26 October amendment adds C and the normalization module. CHAPTER3_AMENDMENT.md supplies replacement text; the original PDF has not been rewritten.
- These human-audit results supplement the archived T07 automated metrics. The older t12_significance_results.csv is a separate historical automated analysis and was not merged into these human results. No held-out answers, dictionary entries, retrieval settings or model outputs were changed.

## Chapter 4 draft interpretation

Across the 20 scenario groups, the three researcher-confirmed independent expert assessments showed ordinal agreement coefficients of .9354 for normalization fidelity, .9112 for answer relevance, and .8732 for factual faithfulness. All exceeded the specified .80 target. Configuration B and C normalization means were 3.7583 and 3.7667 on the five-point scale. On the four-point answer scale, relevance means were 2.3222, 2.2833 and 2.2778 for A, B and C; faithfulness means were 2.7167, 2.7278 and 2.6222. Scenario-paired comparisons did not show statistically significant differences after multiplicity adjustment. Accordingly, this audit supports reporting substantial agreement among the supplied ratings but does not establish superior human-rated performance or an additional dictionary-injection benefit. Provenance, sampling, blinding and exploratory-analysis limitations accompany these conclusions.

## Completion and reproducibility

T10 record consolidation is complete on the researcher's confirmed provenance. T11 calculations are complete and the point-estimate target is met. T12 human-audit comparisons are complete with no significant superiority finding. Completion describes the analysis performed, not an institutional approval or a favorable outcome requirement. No further scoring or model run is needed to reproduce these calculations.

Run scripts/analyze_human_audit.py with a new output version to reproduce; existing completed outputs are protected. Dependencies: the project's Python environment, NumPy, SciPy, and krippendorff 0.8.2 installed only in tmp/t11-analysis-deps. Input hashes, archived input copies, aligned score matrices and scenario aggregates are under private/ and excluded from Git. Public CSVs contain aggregate results. The tracker change log preserves prior cell values.

Method references: manuscript 20260923.pdf, PDF pages 35-36; adviser amendment dated 2026-10-26; Thesis Tracker T10-T12; [Fast Krippendorff implementation](https://github.com/pln-fing-udelar/fast-krippendorff); [SciPy signed-rank documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html). The implementation's ordinal alpha was cross-checked against a separately written coincidence-matrix formula on the actual datasets and 40 random fixtures. The exact signed-rank calculation was checked against brute-force enumeration on four fixtures, including ties and zero differences.
'''
(OUT/'T10_T12_REPORT.md').write_text(report,encoding='utf8')
# Self-contained readable HTML, preserving tables without adding a rendering dependency.
lines=report.splitlines();parts=[];in_table=False
for line in lines:
    if line.startswith('|'):
        if set(line.replace('|','').replace(' ','').replace('-','').replace(':',''))==set():continue
        cells=[x.strip() for x in line.strip('|').split('|')]
        if not in_table:parts.append('<table>');in_table=True;tag='th'
        else:tag='td'
        parts.append('<tr>'+''.join('<'+tag+'>'+html.escape(c)+'</'+tag+'>' for c in cells)+'</tr>');continue
    if in_table:parts.append('</table>');in_table=False
    if line.startswith('# '):parts.append('<h1>'+html.escape(line[2:])+'</h1>')
    elif line.startswith('## '):parts.append('<h2>'+html.escape(line[3:])+'</h2>')
    elif line:parts.append('<p>'+html.escape(line)+'</p>')
if in_table:parts.append('</table>')
(OUT/'T10_T12_REPORT.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Human audit results</title><style>body{font:16px/1.6 system-ui;color:#203040;max-width:1100px;margin:40px auto;padding:0 24px}h1,h2{line-height:1.25}h2{margin-top:36px}table{width:100%;border-collapse:collapse;font-size:14px}th,td{border:1px solid #ccd5df;padding:9px;text-align:left}th{background:#eef3f8}@media print{body{margin:0;font-size:11px}h2{break-after:avoid}tr{break-inside:avoid}}</style>'+''.join(parts)+'</html>',encoding='utf8')
tracker=Path('C:/Users/User/Downloads/thesis_progress_tracker.xlsx')
w=openpyxl.load_workbook(tracker);s=w['Thesis Tracker']
details={
18:('40 normalization pairs; 60 answer triples. Fixed 20 groups; adviser amendment 2026-10-26.','Three two-module packets verified. Post-T07 selection timing disclosed.'),
19:('M1 fidelity 1-5; M2 relevance and faithfulness 1-4. Separate validated exports.','Two-module interface implemented; original Table 2 retained for M2.'),
20:('3 experts: 240 M1 records and 540 M2 records; 1,320 scores validated.','Independent scoring confirmed by researcher. Original provenance correction preserved.'),
21:('Ordinal alpha: fidelity .9354; relevance .9112; faithfulness .8732. Target .80 met.','Analysis complete; cluster-bootstrap CIs and provenance limits in T10_T12_REPORT.md.'),
22:('20 paired scenario groups; seven exact tests with Holm correction. No significant differences.','Exploratory human comparison complete. No superiority established. See paired_comparisons.csv.')}
changes=[]
for row,(requirement,note) in details.items():
    for col,value in [('G','Complete'),('I',requirement),('J',requirement),('K',note)]:
        cell=f'{col}{row}';changes.append(dict(cell=cell,before=s[cell].value,after=value))
payload=dict(source=str(tracker),tab='Thesis Tracker',date='2026-10-28',cells=changes,
             unchanged='Dates, unrelated tasks, other sheets and original source workbook retained. Updated version exported separately.',
             evidence='experiments/t10-t12-human-analysis-v1/T10_T12_REPORT.md')
(OUT/'tracker_changes.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf8')
backup=Path('D:/thesis/conversation-backups/thesis_progress_tracker-before-human-analysis-20261028.xlsx')
if not backup.exists():shutil.copy2(tracker,backup)
assert hashlib.sha256(backup.read_bytes()).hexdigest()==hashlib.sha256(tracker.read_bytes()).hexdigest()
(OUT/'READ_THIS_FIRST.txt').write_text('Human audit analysis completed 2026-10-28.\n\nOpen T10_T12_REPORT.html or T10_T12_REPORT.md for Chapter 4 tables, results and limitations.\nT10: 780 records / 1,320 scores validated, independent scoring confirmed by researcher.\nT11: ordinal alpha .9354, .9112, .8732; all point estimates above .80.\nT12: seven scenario-paired comparisons; no significant difference after Holm adjustment.\n\nOriginal inputs and corrected provenance remain in private/input_snapshot/. No scores changed.\nPrivate files contain individual ratings and architecture mappings; keep them out of public commits.\nUpdated tracker copy: outputs/t10-t12-20261028/thesis_progress_tracker_updated.xlsx. Original Downloads workbook is preserved. See tracker_changes.json.\nNo model or judge rerun, no held-out tuning, no newly invented human scoring.\n',encoding='utf8')
print('Report, chapter tables and exact tracker change log written.')
