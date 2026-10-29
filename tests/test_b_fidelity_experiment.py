"""Guardrails for the isolated post-study development experiment."""
import unittest
from scripts.evaluate_b_fidelity_candidate import fidelity_flags, PROMPT, OUT


class FidelityExperimentTests(unittest.TestCase):
    def test_lost_acronym_is_visible(self):
        self.assertIn('missing_acronym:FSIC', fidelity_flags('FSIC for Occupancy?', 'Occupancy?'))

    def test_number_is_not_matched_inside_another_number(self):
        self.assertIn('missing_number:10', fidelity_flags('10 copies?', '110 copies?'))

    def test_retained_decimal_and_acronym(self):
        self.assertEqual([], fidelity_flags('FSIC at 1.80 m?', 'Is FSIC required at 1.80 m?'))

    def test_extra_output_flag(self):
        self.assertIn('extra_output', fidelity_flags('How much?', 'How much?\nGlossary: extra'))

    def test_empty_output_flag(self):
        self.assertIn('empty_translation', fidelity_flags('Requirements?', ''))

    def test_few_shot_and_isolated_output(self):
        self.assertEqual(PROMPT.count('Citizen Query:'), 2)
        self.assertEqual(OUT.name, 'b-fidelity-development-20261029-v2')


if __name__ == '__main__':
    unittest.main()
