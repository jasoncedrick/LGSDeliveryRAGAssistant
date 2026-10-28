"""Language regression tests with synthetic passages; no benchmark/model calls."""
import unittest
from unittest.mock import Mock
from app import pipeline as frozen
from app.website_language import WebsitePipeline, REQUESTED_LANGUAGE, response_language


class LanguageTests(unittest.TestCase):
    def setUp(self):
        self.pipeline = object.__new__(WebsitePipeline)
        for key, value in dict(endpoint='http://example.invalid', model_name='eboss-mistral',
                               answer_tokens=1536, num_ctx=8192, max_prompt_bytes=6528).items():
            setattr(self.pipeline, key, value)
        self.pipeline.http = Mock()
        self.pipeline.http.post.return_value.json.return_value = {
            'response':'Synthetic explanation [S1].', 'done':True, 'done_reason':'stop', 'eval_count':12}
        self.retrieval = {'context':'[S1] Synthetic source: 5 sets, if applicable.', 'citations':[{'citation':'S1'}]}

    def test_original_question_language(self):
        for query, language in [('ano need magpagawa ng building','taglish'),
                                ('Unsa ang kinahanglan para magpatukod og building?','bislish'),
                                ('What do I need to construct a building?','english')]:
            self.assertEqual(response_language(query), language)

    def test_override_preserves_inputs_settings_and_frozen_prompt(self):
        before = frozen.ANSWER_SYSTEM_PROMPT
        for language in ['taglish','bislish','english']:
            token = REQUESTED_LANGUAGE.set(language)
            try:
                result = self.pipeline._generate_answer('Original inquiry?', self.retrieval)
            finally:
                REQUESTED_LANGUAGE.reset(token)
            payload = self.pipeline.http.post.call_args.kwargs['json']
            self.assertIn('Citizen question:\nOriginal inquiry?', payload['prompt'])
            self.assertIn(self.retrieval['context'], payload['prompt'])
            self.assertEqual(payload['options'], {'temperature':0.,'top_p':0.,'num_predict':1536,'num_ctx':8192})
            self.assertEqual(result['diagnostics']['response_language'], language)
            self.assertTrue(result['diagnostics']['citation_labels_valid'])
        self.assertEqual(frozen.ANSWER_SYSTEM_PROMPT, before)
        self.assertEqual(REQUESTED_LANGUAGE.get(), 'auto')

    def test_extra_instruction_is_counted_in_budget(self):
        self.pipeline.max_prompt_bytes = 1
        result = self.pipeline._generate_answer('ano need?', self.retrieval)
        self.assertEqual(result['status'], 'CONTEXT_BUDGET_EXCEEDED')
        self.pipeline.http.post.assert_not_called()

    def test_exact_fallback_remains_unchanged(self):
        self.pipeline.http.post.return_value.json.return_value['response'] = frozen.FALLBACK_ANSWER
        result = self.pipeline._generate_answer('ano need?', self.retrieval)
        self.assertEqual(result['status'], 'NO_SUPPORTED_ANSWER')
        self.assertEqual(result['answer'], frozen.FALLBACK_ANSWER)


if __name__ == '__main__':
    unittest.main()
