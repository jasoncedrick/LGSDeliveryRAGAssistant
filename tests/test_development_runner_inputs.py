import unittest
from pathlib import Path
from scripts.run_t06_chunk_development import load_development_groups,reference_metadata,score_record,ROOT
class Inputs(unittest.TestCase):
    def test_corrected_groups(self):
        groups=load_development_groups(ROOT/'experiments/t06-formal-development-validation-v3/development_groups.derived.json')
        self.assertEqual(reference_metadata(groups)['mapped_groups'],30)
        self.assertEqual(len(reference_metadata(groups)['mapping_status_counts']),2)
    def test_stopped_query_counts_as_miss(self):
        m=score_record({'ground_truth_chunk_ids':['a'],'retrieved_rankings':{}})
        self.assertEqual(m['3']['hit_at_k'],0)
        self.assertEqual(m['5']['mrr_at_k'],0)
    def test_missing_gold_withheld(self):
        m=score_record({'ground_truth_chunk_ids':[],'retrieved_rankings':{}})
        self.assertEqual(m['3']['status'],'WITHHELD_UNMAPPED_REFERENCES')
if __name__=='__main__': unittest.main()
