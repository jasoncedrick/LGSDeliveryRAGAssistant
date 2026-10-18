"""Development regressions; generation is mocked, not a semantic score."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import numpy as np
from src.answer_checks_v2 import validate_answer, quantities
from src.query_normalizer import QueryNormalizer
from src.section_retriever_v2 import SectionRetrieverV2, ContextBudgetExceeded, route_intent
from app.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]

class SenseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        path = Path(self.tmp.name)/'dict.json'
        path.write_text(json.dumps({'resibo': {'term_id':'DICT-CTO-042',
            'polysemy_flag':True, 'verified_english_definition':'Official Receipt',
            'disambiguation_rule':'Which receipt?'}, 'barangay clearance': {
            'term_id':'DICT-BRGY-101', 'polysemy_flag':True,
            'verified_english_definition':'Barangay clearance'}}))
        self.n = QueryNormalizer(str(path), context_rules_path=str(ROOT/'config/normalization_context_rules_v2.json'))

    def test_explicit_registration_resolves_taglish_and_bislish(self):
        for q in ['Kailan iparehistro ang books of accounts at resibo?',
                  'Kanus-a marehistro ang books of accounts ug resibo human magfile?']:
            with patch('src.query_normalizer.requests.post') as post:
                post.return_value.json.return_value={'response':'Books of accounts and receipts registration deadline'}
                result=self.n.normalize(q)
                self.assertEqual(result['status'],'SUCCESS')
                self.assertEqual(result['resolved_terms'][0]['sense_id'],'merchant_receipt_and_books_registration')
                payload=post.call_args.kwargs['json']
                self.assertIn('Merchant sales receipts',payload['prompt'])
                self.assertEqual(payload['options']['num_predict'],150)

    def test_bare_competing_and_barangay_remain_ambiguous(self):
        for q in ['resibo', 'resibo tax payment register books of accounts',
                  'Asa mukuha ug barangay clearance para sa tindahan?']:
            with patch('src.query_normalizer.requests.post') as post:
                self.assertEqual(self.n.normalize(q)['status'],'FALLBACK_TRIGGERED')
                post.assert_not_called()

    def test_context_rule_does_not_mutate_dictionary(self):
        self.n.scan_query('register books of accounts resibo')
        self.assertEqual(self.n.dictionary['resibo']['verified_english_definition'],'Official Receipt')

class IntentChecks(unittest.TestCase):
    def test_documentary_submission_paraphrase_is_requirements(self):
        self.assertEqual(route_intent('What mandatory documentary submissions are required for pre-assessment?')[0], 'requirements')

    def test_deadline_and_penalty_with_documents_is_mixed(self):
        for q in ['What documents and deadlines apply?', 'Required documents and penalties?', 'Documents and how many days?']:
            self.assertEqual(route_intent(q)[0], 'all')

class AnswerChecks(unittest.TestCase):
    def context(self,text,intent='all'):
        return {'intent':intent,'citations':[{'citation':'S1','text':text}]}

    def test_invented_deadline_is_rejected(self):
        self.assertEqual(validate_answer('Register within 30 days [S1].',self.context('Registration service overview.'))[0],'UNSUPPORTED_QUANTITY')

    def test_exact_source_amount_and_unit_are_accepted(self):
        self.assertIsNone(validate_answer('15 working days; PHP 5,000 [S1].',self.context('Within fifteen (15) working days. Fine: P5,000.')))

    def test_unit_change_is_rejected(self):
        self.assertEqual(validate_answer('15 days [S1]',self.context('15 working days'))[0],'UNSUPPORTED_QUANTITY')

    def test_metadata_cannot_support_quantity(self):
        c=self.context('Overview'); c['citations'][0]['source_page']=30
        self.assertIsNotNone(validate_answer('30 days [S1]',c))

    def test_notarization_and_complete_list(self):
        c=self.context('1. Application\n2. Authorization, notarized by a Notary Public','requirements')
        self.assertEqual(validate_answer('1. Application [S1]\n2. Authorization [S1]',c)[0],'NOTARIZATION_OMITTED')
        self.assertEqual(validate_answer('Application [S1]',c)[0],'CHECKLIST_ITEMS')
        self.assertIsNone(validate_answer('1. Application [S1]\n2. Notarized authorization [S1]',c))

    def test_each_item_needs_its_own_block(self):
        c={'intent':'requirements','citations':[{'citation':'S1','text':'1. Application'}, {'citation':'S2','text':'2. ID'}]}
        self.assertEqual(validate_answer('1. Application [S1]\n2. ID [S1]',c)[0],'ITEM_CITATION')
        self.assertIsNone(validate_answer('1. Application [S1, S2]\n2. ID [S2]',c))

    def test_repeated_sublist_numbers_are_not_forced_linear(self):
        self.assertIsNone(validate_answer('Requirements [S1]',self.context('1. Form\n2. ID\n1. Other form','requirements')))

class CorpusAndPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=ROOT/'data/eboss_corpus_chunks_v2_candidate.json'
        if not path.exists():
            raise unittest.SkipTest('Candidate corpus required; build candidate before testing')
        corpus=json.loads(path.read_text(encoding='utf-8-sig'))
        class Embed:
            def encode(self, labels, **kwargs):
                return np.tile(np.array([[1.,0.]],dtype=np.float32),(len(labels),1))
        cls.r=SectionRetrieverV2(corpus,embedder=Embed())

    def retrieve_selected(self,fragment,intent='all',category='',max_chars=20000):
        s=next(s for s in self.r.sections if fragment in s.key[1] and s.key[3]==category and (s.key[2]=='' if intent=='all' else 'CHECKLIST' in s.key[2]))
        ranked=dict(s.metadata,section_id=s.section_id,label=s.label)
        with patch.object(self.r,'search',return_value={'intent':intent,'ranked_sections':[ranked]}):
            return self.r.retrieve('When must books of accounts be registered?',max_context_chars=max_chars)

    def test_service_context_includes_annex_and_no_other_service(self):
        result=self.retrieve_selected('Registration of Books')
        body='\n'.join(b['text'] for b in result['citations'])
        self.assertIn(('working_day','15'),quantities(body))
        self.assertIn(('money','5E+3'),quantities(body))
        self.assertGreater(result['source_chunk_count'],2)
        ids=set(result['source_chunk_ids'])
        for s in self.r.sections:
            if any(c['chunk_id'] in ids for c in s.chunks):
                self.assertIn('Registration of Books',s.key[1])

    def test_complete_service_budget_refuses_prefix(self):
        with self.assertRaises(ContextBudgetExceeded):
            self.retrieve_selected('Registration of Books',max_chars=100)

    def test_requirements_keep_nine_chunks(self):
        c=self.retrieve_selected('2. Issuance of Business Permit','requirements','NEW')
        self.assertEqual(c['source_chunk_count'],9)

    def make_pipeline(self,context,reply):
        http=SimpleNamespace(post=Mock(return_value=SimpleNamespace(raise_for_status=Mock(),json=Mock(return_value=reply))))
        return Pipeline(normalizer=Mock(),retriever=self.r,http_client=http),http

    def test_incomplete_output_is_preserved_only_in_diagnostics(self):
        c=self.retrieve_selected('2. Issuance of Business Permit','requirements','NEW')
        p,http=self.make_pipeline(c,{'response':'PARTIAL [S1]','eval_count':1536,'done':True,'done_reason':'length'})
        result=p._generate_answer('Unsa ang requirements?',c)
        self.assertEqual(result['status'],'GENERATION_INCOMPLETE')
        self.assertNotIn('PARTIAL',result['answer'])
        self.assertIn('PARTIAL',result['diagnostics']['raw_model_answer'])
        self.assertEqual(http.post.call_args.kwargs['json']['options']['num_predict'],1536)

    def test_both_full_prompts_fit_and_unsupported_draft_is_withheld(self):
        for c in [self.retrieve_selected('Registration of Books'), self.retrieve_selected('2. Issuance of Business Permit','requirements','NEW')]:
            p,http=self.make_pipeline(c,{'response':'30 days [S1]','eval_count':8,'done':True,'done_reason':'stop'})
            result=p._generate_answer('What is the deadline or requirement?',c)
            self.assertTrue(http.post.called,'Full source prompt must fit')
            self.assertEqual(result['status'],'GENERATION_UNSUPPORTED')
            self.assertIn('30 days',result['diagnostics']['raw_model_answer'])

if __name__=='__main__': unittest.main()
