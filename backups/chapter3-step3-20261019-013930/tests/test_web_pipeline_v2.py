"""Web integration contracts. Ollama calls are mocked; no semantic answer score is claimed."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import requests
from fastapi.testclient import TestClient
from app.pipeline import Pipeline, FALLBACK_ANSWER
from app import main as web
from src.query_normalizer import QueryNormalizer
from src.section_retriever_v2 import ContextBudgetExceeded, assemble_context, load_sections

CORPUS = json.loads((ROOT/'data/eboss_corpus_chunks_v2_review.json').read_text(encoding='utf-8-sig'))
SECTIONS = load_sections(CORPUS)


def selected(service='2. Issuance of Business Permit', category='RENEWAL'):
    section = next(s for s in SECTIONS if s.key[1] == service and s.key[3] == category
                   and 'CHECKLIST' in s.key[2])
    context = assemble_context(section)
    return {'status': 'CONTEXT_READY', 'ranked_sections': [dict(section.metadata,
            section_id=section.section_id, label=section.label)], 'scope_notes': [], **context}


def normalizer(**overrides):
    data = {'status': 'SUCCESS', 'normalized_query': 'What are the requirements for business permit renewal?',
            'injected_terms': ['mag renew'], 'clarification_prompt': None}
    data.update(overrides)
    return SimpleNamespace(normalize=Mock(return_value=data))


def response(**overrides):
    data = {'response': 'See the renewal requirements [S1] and [S2].',
            'eval_count': 15, 'done': True, 'done_reason': 'stop'}
    data.update(overrides)
    return SimpleNamespace(raise_for_status=Mock(), json=Mock(return_value=data))


def pipeline(norm=None, context=None, reply=None):
    retriever = SimpleNamespace(sections=SECTIONS,
        retrieve=Mock(return_value=context if context is not None else selected()))
    http = SimpleNamespace(post=Mock(return_value=reply if reply is not None else response()))
    result = Pipeline(normalizer=norm or normalizer(), retriever=retriever, http_client=http)
    return result, retriever, http


class PipelineContracts(unittest.TestCase):
    def test_clarification_returns_without_retrieval_or_generation(self):
        p, retriever, http = pipeline(normalizer(status='FALLBACK_TRIGGERED',
            normalized_query=None, clarification_prompt='Business or individual clearance?'))
        result = p.handle_query('barangay clearance')
        self.assertEqual(result['status'], 'CLARIFICATION_REQUIRED')
        self.assertIsNone(result['normalized_query'])
        self.assertEqual(result['answer'], 'Business or individual clearance?')
        self.assertFalse(result['retrieval_started'])
        self.assertFalse(result['generation_started'])
        retriever.retrieve.assert_not_called()
        http.post.assert_not_called()

    def test_normalizer_failure_or_empty_query_is_explicit(self):
        for bad in [normalizer(normalized_query=''), normalizer(status='OTHER')]:
            p, retriever, http = pipeline(bad)
            with self.assertLogs('app.pipeline', level='WARNING'):
                result = p.handle_query('renewal')
            self.assertEqual(result['status'], 'NORMALIZATION_ERROR')
            self.assertNotEqual(result['answer'], FALLBACK_ANSWER)
            retriever.retrieve.assert_not_called()
            http.post.assert_not_called()
        bad = normalizer()
        bad.normalize.side_effect = ConnectionError('offline')
        p, _, http = pipeline(bad)
        with self.assertLogs('app.pipeline', level='WARNING'):
            self.assertEqual(p.handle_query('renewal')['status'], 'NORMALIZATION_ERROR')
        http.post.assert_not_called()

    def test_full_renewal_and_raw_language_reach_generation_prompt(self):
        p, retriever, http = pipeline()
        result = p.handle_query('Unsa ang requirements para mag renew sa business permit?')
        self.assertEqual(result['status'], 'ANSWERED')
        self.assertEqual(len(result['retrieved_chunk_ids']), 4)
        self.assertTrue(result['context_complete'])
        payload = http.post.call_args.kwargs['json']
        prompt = payload['prompt']
        for phrase in ['if represented', 'if newly designated', '7. Specific requirements',
                       'Unsa ang requirements', '[S1]', '[S2]']:
            self.assertIn(phrase, prompt)
        self.assertTrue(payload['raw'])
        self.assertEqual(payload['options']['num_ctx'], 8192)
        self.assertTrue(all(c['pillar'] == 'Business Bureau' for c in result['retrieved_chunks']))
        self.assertEqual([c['source_page'] for c in result['citations']], [55, 56])
        self.assertEqual(retriever.retrieve.call_args.args[0], result['normalized_query'])

    def test_checklists_larger_than_five_enter_prompt_in_full(self):
        for service, category, count in [
            ('2. Issuance of Business Permit', 'NEW', 9),
            ('Fire Safety Evaluation Clearance (FSEC)',
             'FIRE SAFETY EVALUATION CLEARANCE (FSEC) APPLICATION', 12),
        ]:
            context = selected(service, category)
            p, _, http = pipeline(context=context, reply=response(response='Requirements [S1].'))
            result = p.handle_query('What documents are required?')
            self.assertEqual(result['status'], 'ANSWERED')
            self.assertEqual(len(result['retrieved_chunk_ids']), count)
            prompt = http.post.call_args.kwargs['json']['prompt']
            self.assertIn(context['context'], prompt)
            self.assertIn(context['citations'][-1]['text'], prompt)

    def test_network_errors_do_not_masquerade_as_insufficient_evidence(self):
        p, _, http = pipeline()
        http.post.side_effect = requests.exceptions.ConnectionError('offline')
        with self.assertLogs('app.pipeline', level='WARNING'):
            result = p.handle_query('renewal requirements')
        self.assertEqual(result['status'], 'GENERATION_ERROR')
        self.assertNotEqual(result['answer'], FALLBACK_ANSWER)
        self.assertEqual(result['error']['stage'], 'generation')

    def test_missing_or_invented_citations_and_empty_answers_are_rejected(self):
        for text in ['Unsupported source [S99].', 'No citation at all.', '']:
            p, _, _ = pipeline(reply=response(response=text))
            with self.assertLogs('app.pipeline', level='WARNING'):
                result = p.handle_query('renewal requirements')
            self.assertEqual(result['status'], 'GENERATION_ERROR')
            self.assertNotEqual(result['answer'], text)

    def test_length_limited_answer_is_withheld(self):
        p, _, _ = pipeline(reply=response(response='PARTIAL_CHECKLIST [S1]', done_reason='length'))
        result = p.handle_query('renewal requirements')
        self.assertEqual(result['status'], 'GENERATION_INCOMPLETE')
        self.assertNotIn('PARTIAL_CHECKLIST', result['answer'])

    def test_budget_guards_never_generate_from_a_partial_section(self):
        p, retriever, http = pipeline()
        retriever.retrieve.side_effect = ContextBudgetExceeded('section', 100, 10)
        result = p.handle_query('requirements')
        self.assertEqual(result['status'], 'CONTEXT_BUDGET_EXCEEDED')
        self.assertFalse(result['generation_started'])
        http.post.assert_not_called()
        p, _, http = pipeline()
        p.max_prompt_bytes = 1
        result = p.handle_query('requirements')
        self.assertEqual(result['status'], 'CONTEXT_BUDGET_EXCEEDED')
        self.assertFalse(result['generation_started'])
        http.post.assert_not_called()

    def test_exact_fallback_is_distinct_from_runtime_errors(self):
        p, _, _ = pipeline(reply=response(response=FALLBACK_ANSWER))
        self.assertEqual(p.handle_query('weather tomorrow')['status'], 'NO_SUPPORTED_ANSWER')


class NormalizerConfiguration(unittest.TestCase):
    def test_endpoint_override_preserves_150_token_limit_and_polysemy_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'dictionary.json'
            path.write_text(json.dumps({'barangay clearance': {
                'local_term': 'barangay clearance', 'polysemy_flag': True,
                'disambiguation_rule': 'Which clearance?', 'term_id': 'DICT-BRGY-101',
                'verified_english_definition': 'Barangay clearance'}}))
            n = QueryNormalizer(str(path), ollama_api_url='http://example.test/api/generate', model_name='custom-mistral')
            with patch('src.query_normalizer.requests.post') as post:
                self.assertEqual(n.normalize('barangay clearance')['status'], 'FALLBACK_TRIGGERED')
                post.assert_not_called()
                post.return_value.json.return_value = {'response': 'Business permit requirements', 'eval_count': 4}
                self.assertEqual(n.normalize('permit')['status'], 'SUCCESS')
                self.assertEqual(post.call_args.args[0], 'http://example.test/api/generate')
                self.assertEqual(post.call_args.kwargs['json']['model'], 'custom-mistral')
                self.assertEqual(post.call_args.kwargs['json']['options']['num_predict'], 150)


class ApiContracts(unittest.TestCase):
    def setUp(self):
        self.old = web._state['pipeline']
        self.archive = patch.object(web, 'archive_interaction')
        self.archive.start()
        self.client = TestClient(web.app)

    def tearDown(self):
        self.client.close()
        self.archive.stop()
        web._state['pipeline'] = self.old

    def test_response_preserves_nullable_normalization_and_clarification(self):
        p, _, http = pipeline(normalizer(status='FALLBACK_TRIGGERED', normalized_query=None,
                                         clarification_prompt='Which clearance?'))
        web._state['pipeline'] = p
        response = self.client.post('/api/query', json={'query': 'barangay clearance'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsNone(data['normalized_query'])
        self.assertEqual(data['status'], 'CLARIFICATION_REQUIRED')
        self.assertEqual(data['citations'], [])
        http.post.assert_not_called()

    def test_api_returns_complete_sources_and_answer(self):
        p, _, _ = pipeline()
        web._state['pipeline'] = p
        response = self.client.post('/api/query', json={'query': 'Renewal requirements?'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'ANSWERED')
        self.assertEqual(len(data['retrieved_chunk_ids']), 4)
        self.assertEqual(data['citations'][1]['pdf_relative_page'], 17)
        self.assertIn('latency_seconds', data)
        self.assertTrue(data['context_complete'])
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertEqual(self.client.get('/health').json()['retrieval_mode'], 'experimental_sections_v2')

    def test_input_validation_and_starting_response(self):
        web._state['pipeline'] = None
        self.assertEqual(self.client.post('/api/query', json={'query': 'permit'}).status_code, 503)
        for text in ['', '   ', 'a'*2001]:
            self.assertEqual(self.client.post('/api/query', json={'query': text}).status_code, 422)

    def test_pipeline_is_loaded_once_per_lifespan(self):
        p, _, _ = pipeline()
        with patch.object(web, 'Pipeline', return_value=p) as factory:
            with TestClient(web.app) as client:
                client.get('/health')
                client.get('/health')
                factory.assert_called_once_with()
            self.assertIsNone(web._state['pipeline'])


if __name__ == '__main__':
    unittest.main()
