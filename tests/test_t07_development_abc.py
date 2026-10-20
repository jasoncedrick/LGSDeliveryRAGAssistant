import unittest
from unittest.mock import patch,Mock
from types import SimpleNamespace
from scripts.run_t07_development_abc import InjectionDisabledNormalizer,sparse_retrieval
from src.query_normalizer import QueryNormalizer

class DevelopmentComparisonTests(unittest.TestCase):
    def test_c_retains_conflicts_but_removes_injection(self):
        n=object.__new__(InjectionDisabledNormalizer)
        scan={'matched_entries':[{'local_term':'test'}],'polysemous_triggers':[{'term_id':'test','disambiguation_rule':'Clarify'}],'resolved_terms':[]}
        with patch.object(QueryNormalizer,'scan_query',return_value=scan),patch('src.query_normalizer.requests.post') as post:
            r=n.normalize('test')
        self.assertEqual(r['status'],'FALLBACK_TRIGGERED');self.assertEqual(r['injected_terms'],[]);post.assert_not_called()

    def test_c_sends_empty_glossary_and_same_token_ceiling(self):
        n=object.__new__(InjectionDisabledNormalizer);n.enable_fidelity_contract=False;n.model_name='test';n.ollama_api_url='test'
        scan={'matched_entries':[{'local_term':'test','verified_english_definition':'SECRET DEFINITION'}],'polysemous_triggers':[],'resolved_terms':[]}
        response=Mock();response.json.return_value={'response':'What is test?','done':True}
        with patch.object(QueryNormalizer,'scan_query',return_value=scan),patch('src.query_normalizer.requests.post',return_value=response) as post:
            n.normalize('test')
        payload=post.call_args.kwargs['json']
        self.assertIn('Glossary:\nNone',payload['prompt']);self.assertNotIn('SECRET DEFINITION',payload['prompt']);self.assertEqual(payload['options']['num_predict'],150)

    def test_a_needs_no_dense_or_dictionary_components(self):
        chunks=[{'chunk_id':str(i),'file_source':'source','text_content':str(i),'source_page':1} for i in range(5)]
        sparse=Mock();sparse.get_scores.return_value=[0,3,3,1,0]
        retriever=SimpleNamespace(chunks=chunks,bm25=sparse)
        r=sparse_retrieval(retriever,'Raw QUERY',3)
        self.assertEqual(r['source_chunk_ids'],['1','2','3']);sparse.get_scores.assert_called_once_with(['raw','query']);self.assertEqual(len(r['citations']),3)

if __name__=='__main__':unittest.main()
