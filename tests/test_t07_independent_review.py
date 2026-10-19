import copy
import unittest
from scripts.review_t07_judge_controls import validate_review


class IndependentReviewTests(unittest.TestCase):
    def fixture(self):
        snapshot = dict(items=[dict(audit_id='AUDIT-001', question='fee?', actual_retrieved_context='PHP 500', decision=None, notes='')])
        review = copy.deepcopy(snapshot)
        review.update(independent_human_review_completed=True, review_basis='Human review separate from model outputs.')
        review['items'][0].update(decision='useful', notes='The amount is stated.')
        return review, snapshot

    def test_human_completion_required(self):
        review, snapshot = self.fixture()
        review['independent_human_review_completed'] = False
        with self.assertRaises(ValueError):
            validate_review(review, snapshot)

    def test_source_text_cannot_be_silently_changed(self):
        review, snapshot = self.fixture()
        review['items'][0]['actual_retrieved_context'] = 'PHP 900'
        with self.assertRaises(ValueError):
            validate_review(review, snapshot)

    def test_uncertain_retained_without_forcing_binary_label(self):
        review, snapshot = self.fixture()
        review['items'][0]['decision'] = 'uncertain'
        self.assertEqual(validate_review(review, snapshot), {'AUDIT-001': 'uncertain'})

    def test_duplicate_ids_rejected(self):
        review, snapshot = self.fixture()
        review['items'].append(copy.deepcopy(review['items'][0]))
        with self.assertRaises(ValueError):
            validate_review(review, snapshot)


if __name__ == '__main__':
    unittest.main()
