import json
import unittest
from src.source_span_judge import source_spans, build_request, parse_selection


class SourceSpanTests(unittest.TestCase):
    def test_every_word_and_number_preserved_as_exact_source_pointers(self):
        text = 'PHP 500.00\n  15% café ≤1.80m ' + ' '.join(str(i) for i in range(80))
        spans = source_spans(text)
        for span in spans.values():
            self.assertEqual(span['text'], text[span['start']:span['end']])
        self.assertEqual(' '.join(s['text'] for s in spans.values()).split(), text.split())

    def test_selection_recovers_exact_text_without_model_rewriting(self):
        context = 'Fee: PHP 500.00\nif applicable.'
        spans = source_spans(context)
        value, error = parse_selection(json.dumps(dict(reason='Requested fee.', evidence_span_id='S001')), context, spans)
        self.assertIsNone(error)
        self.assertEqual(value['verdict'], '1')
        self.assertEqual(value['evidence_quotes'], [context])

    def test_negative_and_invalid_never_coerced(self):
        value, error = parse_selection('{"reason":"No fee.","evidence_span_id":"NONE"}', 'Header', source_spans('Header'))
        self.assertEqual(value['verdict'], '0')
        self.assertEqual(value['evidence_quotes'], [])
        value, error = parse_selection('{"reason":"Fee.","evidence_span_id":"S999"}', 'Header', source_spans('Header'))
        self.assertIsNone(value)
        self.assertEqual(error, 'UNKNOWN_SOURCE_SPAN')

    def test_schema_and_prompt_cannot_supply_control_expected_labels(self):
        payload, spans = build_request('q', 'r', 'A source fact.', {})
        self.assertEqual(payload['format']['properties']['evidence_span_id']['enum'], ['NONE', 'S001'])
        self.assertNotIn('expected_verdict', payload['prompt'])
        self.assertEqual(payload['options'], {})


if __name__ == '__main__':
    unittest.main()
