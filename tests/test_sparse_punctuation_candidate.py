import unittest
from scripts.test_normalization_sparse_candidate import tokens

class SparsePunctuationCandidateTests(unittest.TestCase):
    def test_query_and_corpus_acronyms_match_across_punctuation(self):
        self.assertIn('fsif',tokens('How is the fee (FSIF) calculated?'))
        self.assertIn('fsif',tokens('FSIF = 15% of fees'))
        self.assertIn('fsic',tokens('Occupancy)/FSIC (New Business)'))

    def test_unicode_decimal_and_hyphen_values_are_retained(self):
        self.assertEqual(tokens('Café PHP500.00 1.80 2-storey'),['café','php500.00','1.80','2-storey'])

    def test_tokenizer_does_not_expand_or_invent_service_words(self):
        self.assertEqual(tokens('fee/payment (FSIC)'),['fee','payment','fsic'])
        self.assertEqual(tokens(''),[])

if __name__=='__main__':unittest.main()
