"""Version the reviewed chapters and derive human-rating tables without inference."""
import csv
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / 'outputs/manuscript-closeout-20261028'
OUT = ROOT / 'outputs/team-handoff-20261029'
HUMAN = ROOT / 'experiments/t10-t12-human-analysis-v1'


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |'] +
                     ['| ' + ' | '.join(map(str, row)) + ' |' for row in rows])


def main():
    if (OUT / 'CHAPTER_4.md').exists():
        raise FileExistsError('Preserve the completed chapter version; use a new output version.')
    OUT.mkdir(parents=True, exist_ok=True)
    human = json.loads((HUMAN / 'analysis_results.json').read_text())
    aggregate = [r for r in human['descriptives'] if r['language'] == 'all']
    frequency = table(['Dimension', 'Config', 'N', '1', '2', '3', '4', '5'], [
        [r['module'] + ' ' + r['dimension'], r['configuration'], r['rating_count']] +
        [r['score_' + str(i)] if i <= (5 if r['module'] == 'M1' else 4) else '-' for i in range(1, 6)]
        for r in aggregate])
    languages = [r for r in human['descriptives'] if r['module'] == 'M1' and r['language'] != 'all']
    language_table = table(['Config', 'Language', 'Scores', 'Mean', 'Median'], [
        [r['configuration'], r['language'].capitalize(), r['rating_count'], f"{r['mean']:.4f}", f"{r['median']:.0f}"]
        for r in languages])
    c4 = (OLD / 'CHAPTER_4.md').read_text(encoding='utf-8')
    c4 = c4.replace('Table 4.5.', 'Table 4.7.').replace('Table 4.6.', 'Table 4.8.')
    addition = '''
The frequency distribution in Table 4.5 gives the ordinal means a clearer interpretation. In Module 1, 74 of 120 ratings (61.7%) were 4 or 5 for each configuration. These are ratings of 40 outputs by three raters per configuration, not 120 independent citizen inquiries. The remaining ratings include neutral and disagreement responses, so neither configuration preserved every inquiry reliably.

FREQUENCY_TABLE

Table 4.5. Frequencies of the submitted human scores. Module 1 uses 1-5; Module 2 uses 1-4, with a dash for the unavailable fifth category. Counts are repeated ratings by the fixed three-rater panel. No scores were changed or imputed.

LANGUAGE_TABLE

Table 4.6. Descriptive Module 1 fidelity by query language. Each row contains 20 outputs rated by three experts. Language comparisons were not added to the seven primary system tests.

The language breakdown exposes a limitation obscured by the overall mean. Taglish normalization means were 4.5333 for B and 4.5833 for C, whereas Bislish means were 2.9833 and 2.9500. The medians were 5 for Taglish and 3 for Bislish in both configurations. These descriptive differences identify Bislish fidelity as a priority for future investigation; they do not establish a causal language effect or a statistically tested language advantage. The scenario and rater dependence must remain part of any subsequent comparison.

'''.replace('FREQUENCY_TABLE', frequency).replace('LANGUAGE_TABLE', language_table)
    c4 = c4.replace('## 4.6 Answer relevance and factual faithfulness', addition + '## 4.6 Answer relevance and factual faithfulness')
    c4 = c4.replace('Seven distinct outputs were flagged',
        'Scores of 1 or 2 accounted for 108 of 180 relevance ratings (60.0%) for A and 110 of 180 (61.1%) for both B and C. On the stated rubric, these categories indicate an irrelevant answer or one that misses the primary procedural need. For faithfulness, the corresponding counts were 81 (45.0%), 79 (43.9%) and 84 (46.7%). Those categories indicate an unsupported main answer or a major factual error. These proportions describe submitted rating records, not independent failure rates for citizens, but they show why high inter-rater agreement must not be presented as proof that the assistant is ready to provide dependable procedural advice.\n\nSeven distinct outputs were flagged')
    c4 = c4.replace('The app defaults were not automatically promoted to the evaluated configuration. Any demonstration should identify the loaded configuration and corpus rather than implying that every local app run reproduces the archived evaluation.',
        'The later citizen-facing website is a separate post-study implementation with a revised response-language prompt and operational intake experiments. Its exploratory 200-question dry run is not included in the human-score tables or the frozen A/B/C results reported here. Any demonstration must identify the loaded configuration and distinguish operational fixes from the system that produced the archived study outputs.')
    c5 = (OLD / 'CHAPTER_5.md').read_text(encoding='utf-8')
    c5 = c5.replace('Meaning, service, actor direction and explicit qualifiers must therefore be evaluated rather than assumed to survive translation.',
        'Meaning, service, actor direction and explicit qualifiers must therefore be evaluated rather than assumed to survive translation. The descriptive language breakdown further limits an overall fidelity claim: the Module 1 medians were 5 for Taglish and 3 for Bislish in both configurations. A high combined score must not conceal weaker performance on one of the intended language variants.')
    c5 = c5.replace('These results identify limitations in procedural completeness and factual precision rather than establishing uniformly reliable service guidance.',
        'These results identify limitations in procedural completeness and factual precision rather than establishing uniformly reliable service guidance. Approximately 60-61% of relevance ratings and 44-47% of faithfulness ratings fell in categories 1 or 2. The system should therefore be described as a research prototype requiring further validation, even though the experts agreed consistently in their assessments.')
    c5 = c5.replace('Existing app defaults were not automatically synchronized to the evaluated configuration, so operational demonstrations require a configuration check.',
        'The later citizen-facing website uses a separate post-study response-language revision. Its exploratory dry-run findings and subsequent operational changes are not evidence of improvement in the completed human audit or the frozen final evaluation. Operational demonstrations require a configuration check and a separate readiness assessment.')
    c5 = c5.replace('The present results do not justify expanding the dictionary indiscriminately',
        'Future normalization testing should retain balanced Taglish and Bislish samples and report language-specific score distributions. The lower descriptive Bislish fidelity in this panel warrants examination of semantic preservation and natural phrasing under a new development protocol. This recommendation is not a request to change the completed experts\' scores.\n\nThe present results do not justify expanding the dictionary indiscriminately')
    (OUT / 'CHAPTER_4.md').write_text(c4, encoding='utf-8')
    (OUT / 'CHAPTER_5.md').write_text(c5, encoding='utf-8')
    shutil.copytree(OLD / 'figures', OUT / 'figures')
    shutil.copytree(OLD / 'tables', OUT / 'tables')
    shutil.copy2(OLD / 'evidence_tables.json', OUT / 'evidence_tables.json')
    with (OUT / 'tables/human_score_distributions.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(aggregate[0]))
        writer.writeheader(); writer.writerows(aggregate)
    shutil.copy2(ROOT / 'tmp/team-handoff-20261029/human-replay/REPLAY_QA.json', OUT / 'HUMAN_RESULTS_QA.json')
    print('Prepared versioned Chapters 4 and 5 and verified aggregate tables.')


if __name__ == '__main__':
    main()
