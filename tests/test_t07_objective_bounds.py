import unittest
from scripts.review_t07_paired_rescore import ap, bounds


class ObjectiveBoundsTests(unittest.TestCase):
    def test_known_verdicts_and_no_context(self):
        self.assertEqual(bounds([]), (0.0, 0.0))
        self.assertEqual(bounds([0, 1, 0]), (ap([0, 1, 0]), ap([0, 1, 0])))

    def test_all_missing_is_full_range(self):
        low, high = bounds([None, None, None])
        self.assertEqual(low, 0)
        self.assertAlmostEqual(high, 1)

    def test_positive_late_can_reduce_average_precision(self):
        low, high = bounds([1, 0, 0, 0, None])
        self.assertAlmostEqual(low, 0.7)
        self.assertAlmostEqual(high, 1)
        self.assertGreater(high, ap([1, 0, 0, 0, 1]))


if __name__ == '__main__':
    unittest.main()
