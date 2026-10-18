import unittest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock,patch
from src.query_normalizer import translation_errors,QueryNormalizer,BASELINE_SYSTEM_PROMPT


class TranslationContractTests(unittest.TestCase):
    def test_preserved_office_and_expanded_acronym(self):
        self.assertEqual(translation_errors('What is the OCBO FSEC fee?',
            'What is the OCBO Fire Safety Evaluation Clearance (FSEC) fee?',
            {'done':True,'eval_count':20}),[])

    def test_office_substitution_rejected(self):
        self.assertIn('missing_acronym:OCBO',translation_errors(
            'How long does OCBO take?', 'How long does eBOSS take?',{}))

    def test_glossary_contamination_rejected(self):
        self.assertIn('extra_output',translation_errors('What is the fee?',
            'What is the fee?\nGlossary:\nmade up terms',{}))

    def test_truncation_rejected(self):
        for response in [{'done':False},{'done_reason':'length'},{'eval_count':150}]:
            self.assertIn('incomplete_translation',translation_errors('What fee?','What fee?',response))

    def test_empty_rejected(self):
        self.assertIn('empty_translation',translation_errors('What fee?','',{}))

    def test_candidate_retains_invalid_output_and_does_not_search_it(self):
        with tempfile.TemporaryDirectory() as directory:
            dictionary=Path(directory)/'dictionary.json'
            dictionary.write_text(json.dumps({}),encoding='utf-8')
            normalizer=QueryNormalizer(str(dictionary),enable_context_rules=False,enable_fidelity_contract=True)
            response=Mock()
            response.json.return_value={'response':'How long does eBOSS take?','done':True,'eval_count':12}
            with patch('src.query_normalizer.requests.post',return_value=response):
                result=normalizer.normalize('How long does OCBO take?')
            self.assertEqual(result['status'],'ERROR')
            self.assertIsNone(result['normalized_query'])
            self.assertEqual(result['diagnostics']['raw_model_output'],'How long does eBOSS take?')

    def test_default_retains_previous_prompt_and_length_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            dictionary=Path(directory)/'dictionary.json'
            dictionary.write_text('{}',encoding='utf-8')
            normalizer=QueryNormalizer(str(dictionary),enable_context_rules=False)
            response=Mock()
            response.json.return_value={'response':'What is the fee?','eval_count':6}
            with patch('src.query_normalizer.requests.post',return_value=response) as post:
                result=normalizer.normalize('What is the fee?')
            self.assertEqual(result['status'],'SUCCESS')
            payload=post.call_args.kwargs['json']
            self.assertTrue(payload['prompt'].startswith(BASELINE_SYSTEM_PROMPT))
            self.assertTrue(payload['prompt'].endswith('Translated Query:'))
            self.assertEqual(payload['options'],{'temperature':0.0,'top_p':0.0,'num_predict':150})


if __name__=='__main__':unittest.main()
