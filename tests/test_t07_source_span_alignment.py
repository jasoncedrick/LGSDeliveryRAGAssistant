import unittest
from scripts.align_t07_source_spans import locate_span


class AlignmentTests(unittest.TestCase):
    def test_page_artifact_and_typographic_spacing_preserve_source_identity(self):
        span, error = locate_span(dict(source_page=95, text_content='95 City Treasurer s Office fee: PHP 500.00'),
                                  dict(text='City Treasurer’s Office\nfee: PHP 500.00'))
        self.assertIsNone(error)
        self.assertEqual(span[0], 0)

    def test_decimal_change_is_not_identity(self):
        span, error = locate_span(dict(source_page=1, text_content='Rate 0.1%'), dict(text='Rate 01%'))
        self.assertIsNone(span)
        self.assertEqual(error, 'NUMERIC_SIGNATURE_MISMATCH')

    def test_ambiguous_match_and_missing_words_are_not_guessed(self):
        self.assertEqual(locate_span(dict(source_page=1, text_content='fee'), dict(text='fee fee'))[1], 'AMBIGUOUS_SOURCE_OCCURRENCE')
        self.assertEqual(locate_span(dict(source_page=1, text_content='no fee'), dict(text='fee'))[1], 'NO_FULL_SOURCE_IDENTITY')


if __name__ == '__main__':
    unittest.main()
