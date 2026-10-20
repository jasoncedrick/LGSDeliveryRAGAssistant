import unittest
from scripts.calibrate_t07_structured_judge import stats, SCHEMA


class StructuredJudgeCalibrationTests(unittest.TestCase):
    def test_invalid_does_not_become_negative_or_correct(self):
        result = stats([dict(parsed=None, expected_verdict='0', attempts=[{'error': 'INVALID_JSON'}])])
        self.assertEqual(result['invalid'], 1)
        self.assertEqual(result['correct'], 0)
        self.assertEqual(result['FP'], 0)
        self.assertEqual(result['FN'], 0)

    def test_semantic_error_counts_are_separate_from_validity(self):
        result = stats([
            dict(parsed={'verdict': '1'}, expected_verdict='0'),
            dict(parsed={'verdict': '0'}, expected_verdict='1'),
            dict(parsed={'verdict': '1'}, expected_verdict='1'),
        ])
        self.assertEqual((result['valid'], result['correct'], result['FP'], result['FN']), (3, 1, 1, 1))

    def test_schema_does_not_encode_expected_control_answers(self):
        self.assertEqual(SCHEMA['properties']['verdict']['enum'], ['0', '1'])
        self.assertEqual(set(SCHEMA['required']), {'reason', 'verdict', 'evidence_quotes'})
        self.assertFalse(SCHEMA['additionalProperties'])


if __name__ == '__main__':
    unittest.main()
