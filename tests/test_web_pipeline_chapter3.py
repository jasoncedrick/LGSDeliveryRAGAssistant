"""Current web contract with synthetic chunks; no benchmark reads or live LLM calls."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import numpy as np
from fastapi.testclient import TestClient

from app.pipeline import Pipeline, FALLBACK_ANSWER
from app import main as web
from src.chunk_retriever import ChunkRetriever
from src.query_normalizer import QueryNormalizer


def make_pipeline(k=5, reply='The application form is required [S1].', **reply_fields):
    chunks = [{'chunk_id': f'CHUNK-{i}', 'text_content': f'Synthetic requirement number {i}.',
               'file_source': 'synthetic.pdf', 'source_page': 40+i,
               'pdf_relative_page': i+1, 'governance_pillar': 'Synthetic office'} for i in range(6)]
    retriever = ChunkRetriever(chunks, {},
        SimpleNamespace(corpus_size=6, get_scores=lambda q: np.arange(6)),
        SimpleNamespace(ntotal=6, d=2, search=lambda emb, n: (
            np.array([[5.,4.,3.,2.,1.,0.]]), np.array([[5,4,3,2,1,0]]))),
        SimpleNamespace(encode=lambda texts, **kw: np.array([[1.,0.]])),
        {'constraints': {'chunk_tokens':120,'overlap_tokens':20}, 'optimal_top_k': k,
         'optimal_retrieval_weights': {'alpha_bm25':.4,'beta_dense':.6,'gamma_dict':0}})
    normalizer = SimpleNamespace(normalize=Mock(return_value={
        'status':'SUCCESS','normalized_query':'Application requirements','injected_terms':[]}))
    payload = {'response': reply, 'done': True, 'done_reason': 'stop', 'eval_count': 12}
    payload.update(reply_fields)
    http = SimpleNamespace(post=Mock(return_value=SimpleNamespace(
        raise_for_status=Mock(), json=Mock(return_value=payload))))
    with patch.dict(os.environ, {}, clear=True):
        p = Pipeline(normalizer=normalizer, retriever=retriever, http_client=http)
    return p, normalizer, http


class Chapter3PipelineTests(unittest.TestCase):
    def test_only_k_chunks_enter_prompt_and_response(self):
        for k in (3,5):
            p, _, http = make_pipeline(k)
            result = p.handle_query('Unsa ang requirements?')
            self.assertEqual(result['status'],'ANSWERED')
            self.assertEqual(len(result['retrieved_chunk_ids']),k)
            self.assertEqual(len(result['citations']),k)
            self.assertEqual(result['retrieval_mode'],'chapter3_chunks')
            self.assertEqual(result['retrieval_weights']['gamma_dict'],0)
            self.assertNotIn('selected_section',result)
            self.assertNotIn('context_complete',result)
            payload=http.post.call_args.kwargs['json']
            self.assertIn('Unsa ang requirements?',payload['prompt'])
            self.assertNotIn('Synthetic requirement number 0.',payload['prompt'])
            self.assertEqual(payload['options']['temperature'],0)
            self.assertEqual(payload['options']['top_p'],0)
            self.assertTrue(payload['raw'])

    def test_ambiguity_stops_before_retrieval_and_generation(self):
        p, n, http = make_pipeline()
        n.normalize.return_value={'status':'FALLBACK_TRIGGERED','clarification_prompt':'Which receipt?'}
        with patch.object(p.retriever,'retrieve') as retrieval:
            result=p.handle_query('resibo')
            self.assertEqual(result['status'],'CLARIFICATION_REQUIRED')
            retrieval.assert_not_called()
            http.post.assert_not_called()

    def test_offline_evaluation_does_not_replace_generated_claims(self):
        p, _, _=make_pipeline(reply='An unsupported example of 999 days [S99].')
        r=p.handle_query('Application?')
        self.assertEqual(r['answer'],'An unsupported example of 999 days [S99].')
        self.assertFalse(r['diagnostics']['citation_labels_valid'])
        self.assertEqual(r['diagnostics']['faithfulness_evaluation'],'offline_not_performed')
        self.assertEqual(r['diagnostics']['raw_model_answer'],r['answer'])

    def test_incomplete_output_retained_and_labelled(self):
        p, _, _=make_pipeline(reply='Partial answer [S1]',done_reason='length')
        result=p.handle_query('Application?')
        self.assertEqual(result['status'],'GENERATION_INCOMPLETE')
        self.assertEqual(result['answer'],'Partial answer [S1]')

    def test_budget_does_not_silently_drop_chunks(self):
        p, _, http=make_pipeline()
        p.max_prompt_bytes=1
        result=p.handle_query('Application?')
        self.assertEqual(result['status'],'CONTEXT_BUDGET_EXCEEDED')
        self.assertEqual(len(result['retrieved_chunk_ids']),5)
        http.post.assert_not_called()

    def test_invalid_retrieval_is_not_sent_to_generation(self):
        p, _, http=make_pipeline()
        context=p.retriever.retrieve('test')
        context['source_chunk_ids']=context['source_chunk_ids'][:2]
        with patch.object(p.retriever,'retrieve',return_value=context), self.assertLogs('app.pipeline'):
            self.assertEqual(p.handle_query('Application?')['status'],'RETRIEVAL_ERROR')
        http.post.assert_not_called()

    def test_model_empty_response_and_fallback_are_distinct(self):
        p, _, _=make_pipeline(reply='')
        with self.assertLogs('app.pipeline'):
            self.assertEqual(p.handle_query('Application?')['status'],'GENERATION_ERROR')
        p, _, _=make_pipeline(reply=FALLBACK_ANSWER)
        self.assertEqual(p.handle_query('Application?')['status'],'NO_SUPPORTED_ANSWER')

    def test_contextual_rules_can_be_disabled_without_changing_legacy_default(self):
        with tempfile.TemporaryDirectory() as directory:
            dictionary=Path(directory)/'dictionary.json'
            rules=Path(directory)/'rules.json'
            dictionary.write_text(json.dumps({'resibo':{'term_id':'DICT-CTO-042',
                'polysemy_flag':True,'verified_english_definition':'Receipt',
                'disambiguation_rule':'Which receipt?'}}))
            rules.write_text(json.dumps({'schema_version':1,'terms':{'DICT-CTO-042':[
                {'sense_id':'example','english_definition':'Selected sense',
                 'required_any_groups':[['register']]}]}}))
            n=QueryNormalizer(str(dictionary),context_rules_path=str(rules),enable_context_rules=False)
            with patch('src.query_normalizer.requests.post') as post:
                self.assertEqual(n.normalize('register resibo')['status'],'FALLBACK_TRIGGERED')
                post.assert_not_called()
            legacy=QueryNormalizer(str(dictionary),context_rules_path=str(rules))
            self.assertEqual(len(legacy.scan_query('register resibo')['resolved_terms']),1)

    def test_default_factory_uses_paired_artifacts_and_disables_context_rules(self):
        p, _, _=make_pipeline()
        with patch('app.pipeline.ChunkRetriever.from_files',return_value=p.retriever) as factory, \
             patch('app.pipeline.QueryNormalizer') as norm, patch.dict(os.environ,{},clear=True):
            Pipeline()
        args=factory.call_args.kwargs
        self.assertEqual(args['corpus_path'].parent,args['bm25_path'].parent)
        self.assertEqual(args['faiss_path'].parent,args['manifest_path'].parent)
        self.assertFalse(norm.call_args.kwargs['enable_context_rules'])


class Chapter3ApiTests(unittest.TestCase):
    def test_api_archives_scores_sources_and_raw_output(self):
        p, _, _=make_pipeline()
        with patch.object(web,'Pipeline',return_value=p) as factory, \
             patch.object(web,'archive_interaction') as archive:
            with TestClient(web.app) as client:
                response=client.post('/api/query',json={'query':'Application?'})
                self.assertEqual(response.status_code,200)
                data=response.json()
                self.assertEqual(len(data['ranked_chunks']),5)
                self.assertEqual(len(data['citations']),5)
                self.assertEqual(data['pipeline_status'],'development_not_frozen')
                self.assertEqual(data['source_fidelity_status'],'NOT_REVIEWED')
                self.assertEqual(client.get('/health').json()['retrieval_mode'],'chapter3_chunks')
                self.assertEqual(client.get('/').status_code,200)
                factory.assert_called_once_with()
                record=archive.call_args.args[0]
                self.assertEqual(record['diagnostics']['raw_model_answer'],data['answer'])
                self.assertEqual(record['retrieved_chunks'],data['retrieved_chunks'])
                for text in ('','   ','a'*2001):
                    self.assertEqual(client.post('/api/query',json={'query':text}).status_code,422)


if __name__=='__main__':
    unittest.main()
