import unittest
from src.development_retrieval_metrics import ranking_metrics


class RankingTests(unittest.TestCase):
    def test_hit_and_reciprocal_rank(self):
        self.assertEqual(ranking_metrics(['a','b','c'],['b'],3),{'hit_at_k':1,'mrr_at_k':0.5})

    def test_cutoff(self):
        self.assertEqual(ranking_metrics(['a','b','c','d','e'],['d'],3)['hit_at_k'],0)
        self.assertEqual(ranking_metrics(['a','b','c','d','e'],['d'],5)['mrr_at_k'],0.25)

    def test_miss(self):
        self.assertEqual(ranking_metrics(['a','b','c'],['z'],3)['mrr_at_k'],0)

    def test_stopped_query_is_zero_when_labels_exist(self):
        self.assertEqual(ranking_metrics([],['gold'],5),{'hit_at_k':0,'mrr_at_k':0.0})

    def test_missing_gold_not_silent_failure(self):
        with self.assertRaises(ValueError):ranking_metrics(['a'],[],3)

    def test_duplicates_rejected(self):
        with self.assertRaises(ValueError):ranking_metrics(['a','a'],['a'],3)


if __name__=='__main__':unittest.main()
