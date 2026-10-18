import unittest
from scripts.rescore_normalization_intent import intent_failures


class IntentTests(unittest.TestCase):
    def test_human_flagged_duration_to_sequence(self):
        errors=intent_failures('duration','For the occupancy permit, in what order should documents be encoded and received at OCBO?')
        self.assertIn('duration_changed_to_sequence',errors)

    def test_duration_forms(self):
        for text in ['How long does encoding take?','What is the processing duration?','How much time is needed?','How many working days does it take?']:
            self.assertEqual(intent_failures('duration',text),[])

    def test_duration_word_does_not_hide_sequence(self):
        self.assertIn('duration_changed_to_sequence',intent_failures('duration','In what order are duration estimates recorded?'))

    def test_quantity_not_cost(self):
        self.assertTrue(intent_failures('quantity','How much do the building plans cost?'))
        self.assertEqual(intent_failures('quantity','How many building-plan sets are required?'),[])

    def test_amount_not_payment_location(self):
        self.assertTrue(intent_failures('fee_amount','Where do I pay the fee?'))
        self.assertEqual(intent_failures('fee_amount','What is the monetary settlement for washing pigs?'),[])

    def test_time_unit_alternatives(self):
        self.assertEqual(intent_failures('time_unit_alternative','Does processing use calendar days or working days?'),[])
        self.assertTrue(intent_failures('time_unit_alternative','Does it take working days?'))

    def test_no_silent_success_for_unknown_intent(self):
        self.assertEqual(intent_failures(None,'Anything?'),['intent_not_specified'])


if __name__=='__main__':unittest.main()
