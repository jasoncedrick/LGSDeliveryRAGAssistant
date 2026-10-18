import unittest
from scripts.run_normalization_fidelity_suite import cases,checks


class SuiteScoringTests(unittest.TestCase):
    def test_complete_multilingual_groups_and_unique_ids(self):
        data=cases()
        self.assertEqual(len({c['id'] for c in data}),24)
        for group in {c['question_group_id'] for c in data[:18]}:
            self.assertEqual({c['language'] for c in data if c['question_group_id']==group},
                             {'English','Bislish','Taglish'})

    def test_missing_service_and_action_detected(self):
        case=cases()[0]
        result=checks(case,{'status':'SUCCESS','normalized_query':'What is the OCBO building permit duration?'})
        self.assertIn('missing_concept:service',result['automatic_failures'])
        self.assertIn('missing_concept:receiving',result['automatic_failures'])

    def test_negation_is_required(self):
        case=cases()[15]
        result=checks(case,{'status':'SUCCESS','normalized_query':'Locational clearance requirements for a two-storey and three-storey building?'})
        self.assertIn('missing_concept:negation',result['automatic_failures'])

    def test_dictionary_fallback_needs_prompt(self):
        result=checks(cases()[18],{'status':'FALLBACK_TRIGGERED','normalized_query':None})
        self.assertIn('missing_clarification',result['automatic_failures'])

    def test_exact_copy_is_distinct_from_concept_coverage(self):
        case=cases()[0]
        result=checks(case,{'status':'SUCCESS','normalized_query':case['query']})
        self.assertTrue(result['automatic_checks_passed'])
        self.assertTrue(result['english_wording_preserved'])


if __name__=='__main__':unittest.main()
