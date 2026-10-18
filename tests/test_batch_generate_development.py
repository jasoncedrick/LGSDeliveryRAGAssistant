import unittest
from scripts.batch_generate_development import context_from_saved


class ContextArchiveTests(unittest.TestCase):
    def setUp(self):
        self.chunks={str(i):{'text_content':'fact '+str(i),'source_page_id':'P1','file_source':'source.pdf','source_page':7,'pdf_relative_page':1} for i in range(3)}
        self.row={'k':3,'returned':[{'chunk_id':str(i),'text':'fact '+str(i),'source_page_id':'P1'} for i in range(3)]}

    def test_order_and_exact_text(self):
        result=context_from_saved(self.row,self.chunks)
        self.assertEqual([x['chunk_id'] for x in result['citations']],['0','1','2'])
        self.assertIn('[S2] source.pdf',result['context'])

    def test_modified_text_refused(self):
        self.row['returned'][0]['text']='wrong text'
        with self.assertRaises(ValueError):context_from_saved(self.row,self.chunks)

    def test_duplicate_refused(self):
        self.row['returned'][1]=self.row['returned'][0]
        with self.assertRaises(ValueError):context_from_saved(self.row,self.chunks)


if __name__=='__main__':unittest.main()
