import unittest
from scripts.stage_table_repairs import insert_annotations


class SourcePreservationTests(unittest.TestCase):
    def test_preserves_spacing_and_other_content(self):
        source='NOTE (1): keep exactly\nA  document\nUnrelated footer'
        result,ledger=insert_annotations(source,[('A document','mapped service')])
        self.assertEqual(result.replace(ledger[0]['inserted_text'],'',1),source)
        self.assertEqual(result.count('A  document'),1)

    def test_duplicate_label_rejected(self):
        with self.assertRaises(ValueError):
            insert_annotations('A document\nA document',[('A document','mapping')])

    def test_missing_label_rejected(self):
        with self.assertRaises(ValueError):
            insert_annotations('Original text',[('Missing text','mapping')])

    def test_overlapping_labels_rejected(self):
        with self.assertRaises(ValueError):
            insert_annotations('A document',[('A document','one'),('document','two')])


if __name__=='__main__':
    unittest.main()
