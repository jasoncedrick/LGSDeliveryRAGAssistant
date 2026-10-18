import unittest
from scripts.score_development_ragas import finite_score


class JudgeFailureTests(unittest.TestCase):
    def test_failed_scores_are_null_not_zero(self):
        for value in [float('nan'),float('inf'),None,'invalid']:
            self.assertIsNone(finite_score(value))

    def test_zero_is_valid_score(self):
        self.assertEqual(finite_score(0),0.0)
        self.assertEqual(finite_score(0.75),0.75)


if __name__=='__main__':unittest.main()
