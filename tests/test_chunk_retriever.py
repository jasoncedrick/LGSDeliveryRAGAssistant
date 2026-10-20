"""Independent synthetic checks; never reads development or held-out benchmarks."""
import unittest
from copy import deepcopy
from types import SimpleNamespace

import numpy as np

from src.chunk_retriever import ChunkRetriever, audit_chunk_tokens, min_max_normalize


class ChunkRetrieverTests(unittest.TestCase):
    def setUp(self):
        self.chunks = [
            {'chunk_id': f'C{i}', 'text_content': text, 'file_source': 'synthetic.pdf',
             'source_page': i + 1, 'pdf_relative_page': i + 1, 'token_count': 3}
            for i, text in enumerate(['permit permit application', 'general procedure text',
                                      'permit fee payment', 'other service text',
                                      'unrelated office text'])]
        self.manifest = {
            'constraints': {'chunk_tokens': 120, 'overlap_tokens': 20},
            'optimal_top_k': 3,
            'optimal_retrieval_weights': {'alpha_bm25': .4, 'beta_dense': .4, 'gamma_dict': .2}}
        self.bm25 = SimpleNamespace(corpus_size=5,
                                   get_scores=lambda tokens: [10, 0, 5, 0, 0])
        # Deliberately return dense scores in ranked order, not corpus order.
        self.index = SimpleNamespace(ntotal=5, d=2, search=lambda emb, k: (
            np.array([[1., .5, .25, 0., 0.]]), np.array([[1, 2, 0, 3, 4]])))
        self.embedder = SimpleNamespace(encode=lambda texts, **kw: np.array([[1., 0.]]))

    def retriever(self):
        return ChunkRetriever(self.chunks, {'permit': {}}, self.bm25, self.index,
                              self.embedder, self.manifest)

    def test_hand_calculated_fusion_and_dense_row_mapping(self):
        result = self.retriever().retrieve('permit')
        # C0=.4*1+.4*.25+.2*1=.7; C2=.4*.5+.4*.5+.2*1=.6; C1=.4.
        self.assertEqual(result['source_chunk_ids'], ['C0', 'C2', 'C1'])
        np.testing.assert_allclose([r['final_score'] for r in result['ranked_chunks']],
                                   [.7, .6, .4])
        self.assertEqual(result['candidate_count'], 5)
        self.assertEqual(len(result['citations']), 3)
        self.assertEqual(result['citations'][1]['text'], self.chunks[2]['text_content'])
        self.assertNotIn('other service text', result['context'])

    def test_zero_dictionary_weight_is_preserved(self):
        self.manifest['optimal_retrieval_weights'] = {
            'alpha_bm25': .4, 'beta_dense': .6, 'gamma_dict': 0}
        result = self.retriever().retrieve('permit')
        self.assertEqual(result['source_chunk_ids'], ['C1', 'C0', 'C2'])
        np.testing.assert_allclose([r['final_score'] for r in result['ranked_chunks']],
                                   [.6, .55, .5])
        self.assertEqual(result['weights']['gamma_dict'], 0)

    def test_constant_scores_and_no_dictionary_match(self):
        np.testing.assert_array_equal(min_max_normalize([2, 2, 2]), [0, 0, 0])
        result = self.retriever().retrieve('unknown', top_k=5)
        self.assertEqual(len(result['source_chunk_ids']), 5)
        self.assertEqual(result['matched_dictionary_terms'], [])
        self.assertTrue(all(r['normalized_scores']['dictionary'] == 0
                            for r in result['ranked_chunks']))

    def test_invalid_k_weights_and_chunk_configuration(self):
        for k in (0, 1, 4, 6, True, 3.0):
            with self.assertRaises(ValueError):
                self.retriever().retrieve('permit', top_k=k)
        for weights in [(-.1, .6, .5), (.4, .6, .2), (float('nan'), 0, 1)]:
            self.manifest['optimal_retrieval_weights'] = dict(zip(
                ('alpha_bm25', 'beta_dense', 'gamma_dict'), weights))
            with self.assertRaises(ValueError):
                self.retriever()
        self.manifest['constraints']['chunk_tokens'] = 200
        with self.assertRaises(ValueError):
            self.retriever()

    def test_index_mismatch_and_invalid_dense_rows(self):
        self.index.ntotal = 4
        with self.assertRaises(ValueError):
            self.retriever()
        self.index.ntotal = 5
        self.index.search = lambda emb, k: (np.zeros((1, 5)), np.array([[0, 1, 2, 3, -1]]))
        with self.assertRaises(ValueError):
            self.retriever().retrieve('permit')

    def test_stable_ties_and_inputs_remain_unchanged(self):
        original = deepcopy(self.chunks)
        self.bm25.get_scores = lambda tokens: np.ones(5)
        self.index.search = lambda emb, k: (np.ones((1, 5)), np.array([[4, 3, 2, 1, 0]]))
        result = self.retriever().retrieve('unknown')
        self.assertEqual(result['source_chunk_ids'], ['C0', 'C1', 'C2'])
        self.assertEqual(self.chunks, original)

    def test_token_audit_uses_actual_text(self):
        tokenizer = SimpleNamespace(encode=lambda text, **kw: text.split())
        self.assertTrue(audit_chunk_tokens(self.chunks, tokenizer)['passes_text_length_validation'])
        self.chunks[0]['text_content'] = ' '.join(['token'] * 121)
        self.chunks[0]['token_count'] = 120
        audit = audit_chunk_tokens(self.chunks, tokenizer)
        self.assertFalse(audit['passes_text_length_validation'])
        self.assertEqual(audit['actual_max_tokens'], 121)
        self.assertEqual(audit['invalid_length_count'], 1)
        self.assertEqual(audit['stored_count_mismatch_count'], 1)

    def test_real_bm25_and_faiss_with_synthetic_vectors(self):
        import faiss
        from rank_bm25 import BM25Okapi

        self.bm25 = BM25Okapi([c['text_content'].split() for c in self.chunks])
        self.index = faiss.IndexFlatIP(2)
        self.index.add(np.asarray([[1, 0], [0, 1], [2**-.5, 2**-.5],
                                   [-1, 0], [0, -1]], dtype=np.float32))
        result = self.retriever().retrieve('permit')
        self.assertEqual(result['source_chunk_ids'], ['C0', 'C2', 'C1'])
        self.assertAlmostEqual(result['ranked_chunks'][0]['raw_scores']['dense'], 1)
        self.assertAlmostEqual(result['ranked_chunks'][1]['raw_scores']['dense'], 2**-.5)


if __name__ == '__main__':
    unittest.main()
