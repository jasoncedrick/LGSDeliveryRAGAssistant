import unittest
from scripts.prepare_t07_final_evaluation import check_groups


class FinalPreflightTests(unittest.TestCase):
    def groups(self):
        return [dict(group_id=f'TEST-{i}', pillar=str(i // 14), split='test',
            ground_truth_chunk_ids=['ACTIVE-001'], ground_truth_reference_answer='A source fact.',
            queries=dict(english='q', taglish='q', bislish='q')) for i in range(70)]

    def test_matching_frozen_ids_and_partition(self):
        self.assertTrue(check_groups(self.groups(), {'ACTIVE-001'}, {'DEV-001'})['ready'])

    def test_legacy_gold_is_blocker_not_silent_miss(self):
        result = check_groups(self.groups(), {'OTHER-ID'}, set())
        self.assertFalse(result['ready'])
        self.assertEqual(result['affected_groups'], 70)
        self.assertIn('GOLD_IDS_NOT_IN_FROZEN_CORPUS', result['errors'])

    def test_group_overlap_blocks_final_run(self):
        self.assertIn('DEVELOPMENT_TEST_GROUP_OVERLAP', check_groups(self.groups(), {'ACTIVE-001'}, {'TEST-0'})['errors'])

    def test_missing_language_is_not_silently_excluded(self):
        groups = self.groups()
        del groups[0]['queries']['bislish']
        self.assertFalse(check_groups(groups, {'ACTIVE-001'}, set())['ready'])


if __name__ == '__main__':
    unittest.main()
