"""Post-study intake and prompt contracts; synthetic text, no model calls."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.website_intake import intake_message, localize_clarification
from app.website_language import WebsitePipeline, REQUESTED_LANGUAGE, response_language
from app.website_normalizer import WebsiteNormalizer


class GroundingTests(unittest.TestCase):
    def test_missing_service_and_context_never_retrieves(self):
        pipeline=object.__new__(WebsitePipeline)
        pipeline.normalizer=Mock()
        for query in ['How much will I pay?', 'Ano requirements po?', 'Asa ko moadto ani?',
                      'I need a clearance.', 'Renewal lang po, ano dadalhin?',
                      'Can my sister do it for me?', "What if I'm only renting the space?"]:
            result=pipeline.handle_query(query)
            self.assertEqual(result['status'],'CLARIFICATION_REQUIRED',query)
            self.assertFalse(result['generation_started'])
        pipeline.normalizer.normalize.assert_not_called()

    def test_supported_topics_still_reach_pipeline(self):
        for query in ['Who signs the building plans?', 'What documents do I need for a business permit?',
                      'Pila ka sets sa building plans ang ipasa sa CPDO?', 'Unsa requirements sa cedula?',
                      'Do I need a fire clearance for welding?', 'What does UEESZ mean?']:
            self.assertIsNone(intake_message(query,'english'),query)
        self.assertIsNone(intake_message('Is an SSS document required for a business permit?','english'))

    def test_capabilities_and_outside_scope(self):
        for query in ['Can you approve my business permit here?', 'Pwede diri nako i-send akong payment para permit?',
                      'Can you check my actual application status?']:
            self.assertEqual(intake_message(query,'english')[0],'CAPABILITY_LIMIT')
        for query in ['Asa ko mag register sa SSS?', "Where can I renew my passport?", 'Unsa forecast sa ulan ugma?']:
            self.assertEqual(intake_message(query,'english')[0],'OUT_OF_SCOPE')

    def test_language_clues_and_explicit_override(self):
        for query,expected in [('Anong papers ang dadalhin pag magbabayad ng amilyar?','taglish'),
                               ('Sino ang pipirma sa certificate of completion ng building?','taglish'),
                               ('Gi-deny akong locational clearance. Pwede ba ko mo-appeal?','bislish'),
                               ('Need ba nako dalhon ang original ID?','bislish'),
                               ('Can you approve my business permit here?','english')]:
            self.assertEqual(response_language(query),expected)
            self.assertEqual(response_language(query,'english'),'english')

    def test_clarification_preserves_both_options(self):
        raw='Did you mean [Option A: Individual Community Tax Certificate (Cedula)] or [Option B: Corporate Community Tax Certificate]?'
        for language in ['taglish','bislish','english']:
            answer=localize_clarification(raw,language)
            self.assertIn('Individual Community Tax Certificate (Cedula)',answer)
            self.assertIn('Corporate Community Tax Certificate',answer)
        self.assertTrue(localize_clarification(raw,'bislish').startswith('Asa niini'))

    def test_explicit_choice_only_no_guessing_or_dictionary_mutation(self):
        class Base:
            dictionary={'cedula':{'term_id':'test','polysemy_flag':True,
                        'disambiguation_rule':'Did you mean [Option A: Individual Community Tax Certificate] or [Option B: Corporate Community Tax Certificate]?',
                        'verified_english_definition':'Community Tax Certificate'}}
            def normalize(self,query):
                return {'status':'FALLBACK_TRIGGERED' if self.dictionary['cedula']['polysemy_flag'] else 'SUCCESS'}
        base=Base();normalizer=WebsiteNormalizer(base)
        self.assertEqual(normalizer.normalize('cedula for work')['status'],'FALLBACK_TRIGGERED')
        self.assertEqual(normalizer.normalize('cedula (Individual Community Tax Certificate)')['status'],'SUCCESS')
        self.assertTrue(base.dictionary['cedula']['polysemy_flag'])
        self.assertEqual(normalizer.normalize('cedula Individual Community Tax Certificate or Corporate Community Tax Certificate')['status'],'FALLBACK_TRIGGERED')

    def test_real_dictionary_option_can_complete_clarification(self):
        from pathlib import Path
        from src.query_normalizer import QueryNormalizer
        dictionary=Path(__file__).resolve().parents[1]/'data/municipal_dictionary_v1.json'
        base=QueryNormalizer(str(dictionary),enable_context_rules=False,enable_fidelity_contract=False)
        adapter=WebsiteNormalizer(base)
        first=adapter.normalize('Unsa requirements sa cedula?')
        self.assertEqual(first['status'],'FALLBACK_TRIGGERED')
        option='Individual Community Tax Certificate (Cedula)'
        response=Mock();response.json.return_value={'response':'What are the requirements for an Individual Community Tax Certificate?','done':True,'eval_count':14}
        with patch('src.query_normalizer.requests.post',return_value=response) as post:
            selected=adapter.normalize('Unsa requirements sa cedula? ('+option+').')
        self.assertEqual(selected['status'],'SUCCESS')
        self.assertEqual(post.call_count,1)
        self.assertIn(option,post.call_args.kwargs['json']['prompt'])
        self.assertEqual(adapter.normalize('Unsa requirements sa cedula?')['status'],'FALLBACK_TRIGGERED')

    def test_prompt_keeps_exact_selected_text_without_internal_headers(self):
        pipeline=object.__new__(WebsitePipeline)
        for k,v in dict(endpoint='http://example.invalid',model_name='eboss-mistral',answer_tokens=1536,num_ctx=8192,max_prompt_bytes=6528).items():setattr(pipeline,k,v)
        pipeline.http=Mock();pipeline.http.post.return_value.json.return_value={'response':'A supported fact [S1].','done':True,'eval_count':10}
        passage='For a business permit, if represented, submit ONE original. This is not a universal requirement.'
        retrieval={'context':'[S1] file | chunk DEV120-PRIVATE\n'+passage,'citations':[{'citation':'S1','chunk_id':'DEV120-PRIVATE','file_source':'test.pdf','pdf_relative_page':1,'text':passage}]}
        result=pipeline._generate_answer('How many copies for this business permit?',retrieval)
        sent=pipeline.http.post.call_args.kwargs['json']
        self.assertIn(passage,sent['prompt']);self.assertNotIn('DEV120-PRIVATE',sent['prompt'])
        self.assertIn('DEV120-PRIVATE',retrieval['context'])
        self.assertIn('Never invent a permission or exception',sent['prompt'])
        self.assertEqual(sent['options'],{'temperature':0.,'top_p':0.,'num_predict':1536,'num_ctx':8192})
        self.assertEqual(pipeline.http.post.call_count,1)
        self.assertIn(passage,result['diagnostics']['generation_context'])

    def test_scope_checks_fail_closed_without_reranking(self):
        from app.website_scope import coverage_issue
        sources=[{'file_source':'OCBD charter.pdf','text':'Architectural Permit: five sets of plans.'}]
        self.assertEqual(coverage_issue('How many plan sets for CPDO?',sources),'requested_office_absent:CPDO')
        self.assertEqual(coverage_issue('Is a business permit needed for online selling?',sources),'requested_topic_absent')
        self.assertEqual(coverage_issue('Do I need a hot-work clearance for welding?',sources),'requested_topic_absent')
        # Unrelated business chronology must not support a housing-sequence claim.
        sources=[{'text':'Building Permit Form: if City housing, use City signatory.'},
                 {'text':'First secure a business permit and pay the fees.'}]
        self.assertEqual(coverage_issue('I will build a small house. Which permit first?',sources),'requested_sequence_absent')
        self.assertIsNone(coverage_issue('How many copies for a business permit?',[
            {'text':'Business Permit checklist: one original copy, if represented.'}]))

    def test_scope_abstention_makes_no_generation_call(self):
        pipeline=object.__new__(WebsitePipeline);pipeline.http=Mock()
        result=pipeline._generate_answer('How many sets for CPDO?',{'citations':[{
            'file_source':'OCBD charter.pdf','text':'Five sets.'}],'context':'unchanged'})
        self.assertEqual(result['status'],'NO_SUPPORTED_ANSWER')
        self.assertFalse(result['generation_started'])
        pipeline.http.post.assert_not_called()


if __name__=='__main__':unittest.main()
