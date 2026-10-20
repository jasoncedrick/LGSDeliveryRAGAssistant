import unittest
from scripts.consolidate_t07_saved_results import summarize


class SavedSummaryTests(unittest.TestCase):
    def test_zero_retained_and_missing_not_imputed(self):
        self.assertEqual(summarize([0.0, None, 1.0]), {'mean': 0.5, 'valid': 2, 'missing': 1})

    def test_all_missing_not_zero(self):
        self.assertEqual(summarize([None]), {'mean': None, 'valid': 0, 'missing': 1})

    def test_nonfinite_value_rejected(self):
        with self.assertRaises(ValueError):
            summarize([float('nan')])


if __name__ == '__main__':
    unittest.main()
