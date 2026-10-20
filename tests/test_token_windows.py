"""Synthetic boundary/provenance tests; no benchmark access or model downloads."""
import hashlib
import unittest
from copy import deepcopy

from src.token_windows import source_windows, verify_source_windows, prepare_window_ids


class CharacterTokenizer:
    """One token per character for independently countable boundary tests."""
    cls_token_id = 0
    sep_token_id = 1
    def __call__(self, text, **kwargs):
        return {'input_ids': self.encode(text),
                'offset_mapping': [(i, i+1) for i in range(len(text))]}

    def encode(self, text, **kwargs):
        return [ord(c) for c in text]

    def build_inputs_with_special_tokens(self, ids):
        return [0] + ids + [1]


class TokenWindowTests(unittest.TestCase):
    def setUp(self):
        self.tokenizer = CharacterTokenizer()
        self.text = ''.join(chr(65+i % 26) for i in range(241))
        self.page = {'source_page_id': 'TEST-P1', 'text': self.text,
                     'text_sha256': hashlib.sha256(self.text.encode()).hexdigest(),
                     'file_source': 'synthetic.pdf', 'pdf_relative_page': 1,
                     'source_page': 99, 'pdf_sha256': 'synthetic'}
        self.chunks = [{**{k:v for k,v in self.page.items() if k not in ('text', 'text_sha256')},
                        **window, 'chunk_id': f'C{i}'}
                       for i, window in enumerate(source_windows(self.text, self.tokenizer))]

    def test_exact_120_windows_stride_100_and_tail(self):
        self.assertEqual([c['token_count'] for c in self.chunks], [120, 120, 41])
        self.assertEqual([c['token_start'] for c in self.chunks], [0, 100, 200])
        report = verify_source_windows(self.chunks, [self.page], self.tokenizer)
        self.assertTrue(report['passed'])
        self.assertEqual(report['verified_overlap_pairs'], 2)
        self.assertEqual(report['max_embedding_input_tokens'], 122)
        reconstructed = self.chunks[0]['text_content'] + ''.join(c['text_content'][20:] for c in self.chunks[1:])
        self.assertEqual(reconstructed, self.text)

    def test_short_page_and_exact_boundary_do_not_create_redundant_tail(self):
        for size, expected in [(0, []), (20, [20]), (120, [120]),
                               (121, [120, 21]), (220, [120, 120])]:
            windows = list(source_windows('a'*size, self.tokenizer))
            self.assertEqual([w['token_count'] for w in windows], expected)

    def test_rejects_missing_window_and_mutated_token_text_or_metadata(self):
        with self.assertRaises(ValueError):
            verify_source_windows(self.chunks[:-1], [self.page], self.tokenizer)
        for field, value in [('embedding_input_ids', [999]*120), ('text_content', 'changed'),
                             ('token_start', 101), ('source_page', 10)]:
            bad = deepcopy(self.chunks)
            bad[1][field] = value
            with self.assertRaises(ValueError):
                verify_source_windows(bad, [self.page], self.tokenizer)

    def test_real_cached_tokenizer_preserves_midword_token_ids(self):
        from transformers import AutoTokenizer
        from src.chunk_retriever import MODEL_NAME

        tok = AutoTokenizer.from_pretrained(MODEL_NAME, local_files_only=True)
        text = ('The notarized application identifies the business location. ' * 60).strip()
        ids = tok.encode(text, add_special_tokens=False)
        windows = list(source_windows(text, tok))
        for i, w in enumerate(windows):
            self.assertEqual(w['embedding_input_ids'], ids[i*100:i*100+120])
            self.assertLessEqual(len(prepare_window_ids(w['embedding_input_ids'], tok)), 122)
            if i:
                self.assertEqual(windows[i-1]['embedding_input_ids'][-20:], w['embedding_input_ids'][:20])

    def test_special_tokens_match_actual_cached_tokenizer(self):
        from transformers import AutoTokenizer
        from src.chunk_retriever import MODEL_NAME

        tok = AutoTokenizer.from_pretrained(MODEL_NAME, local_files_only=True)
        text = 'Application for a business permit.'
        ids = tok.encode(text, add_special_tokens=False)
        self.assertEqual(prepare_window_ids(ids, tok), tok.encode(text))
        self.assertEqual(len(prepare_window_ids([10]*120, tok)), 122)


if __name__ == '__main__':
    unittest.main()
