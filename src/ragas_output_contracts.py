"""Opt-in evaluator-only prompt suffixes; never repair or replace judge verdicts."""
VERSION = 'ragas-output-contract-v1'
INSTRUCTIONS = {
    'context_precision': (
        'Return exactly ONE top-level JSON object with exactly two fields: '
        '"reason" (a string) and "verdict" (the string "0" or "1"). '
        'Do not nest these fields under verification or another field. '
        'Do not return an array, multiple objects, markdown, or extra prose. '
        'Apply the original usefulness criterion; this instruction changes output format only.'
    ),
    'answer_relevancy': (
        'Return exactly ONE top-level JSON object for this invocation with exactly two fields: '
        '"question" (one generated question as a string) and "noncommittal" (the integer 0 or 1). '
        'Use the key question, not answer. Do not copy the context or provide an answer. '
        'Do not return an array, multiple objects, markdown, or extra prose. '
        'The evaluator requests multiple generations separately; produce only one object here. '
        'Apply the original question-generation and noncommittal criteria; change output format only.'
    ),
}


def apply_contracts(metrics):
    for name, field in [('context_precision', 'context_precision_prompt'),
                        ('answer_relevancy', 'question_generation')]:
        if name in metrics:
            getattr(metrics[name], field).instruction += '\n' + INSTRUCTIONS[name]
    return {'version': VERSION, 'instructions': dict(INSTRUCTIONS)}
