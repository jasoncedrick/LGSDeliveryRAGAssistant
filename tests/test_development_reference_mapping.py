import unittest
from scripts.validate_formal_development import tokens,span_occurrences


class ReferenceMappingTests(unittest.TestCase):
    def test_unicode_punctuation_is_spacing(self):
        self.assertEqual(tokens('Mayor’s Permit'),tokens('Mayor s Permit'))

    def test_boundary_word_fragments_allowed(self):
        self.assertEqual(span_occurrences(tokens('Sketch Google map of location'),tokens('ch Google map of loc')), [0])

    def test_interior_word_changes_rejected(self):
        self.assertEqual(span_occurrences(tokens('Sketch Google map of location'),tokens('ch other map of loc')), [])

    def test_short_fragment_not_used_as_gold(self):
        self.assertEqual(span_occurrences(tokens('Documents received'),tokens('ments received')), [])


if __name__=='__main__':unittest.main()
