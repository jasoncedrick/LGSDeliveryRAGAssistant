"""Website integration checks use synthetic answers, never held-out queries."""
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from app.website import Runtime, create_app, registered_profile, public_result


class WebsiteTests(unittest.TestCase):
    def setUp(self):
        self.runtime=Runtime()
        self.runtime.pipeline=SimpleNamespace(handle_query=Mock(return_value={
            'status':'ANSWERED','answer':'Synthetic response [S1].','citations':[],
            'diagnostics':{'citation_labels_valid':True,'raw_model_answer':'not public'}}))
        self.runtime.health=Mock(return_value={'status':'ready','message':'Ready'})
        self.client=TestClient(create_app(self.runtime,start_runtime=False))

    def test_source_library_and_allowlist(self):
        sources=self.client.get('/api/sources').json()
        self.assertEqual(len(sources),5)
        for source in sources:
            r=self.client.get(source['url']);self.assertEqual(r.status_code,200);self.assertTrue(r.content.startswith(b'%PDF'))
        self.assertEqual(self.client.get('/sources/unknown.pdf').status_code,404)
        self.assertEqual(self.client.get('/sources/%2e%2e%2f.gitignore.pdf').status_code,404)

    def test_cors_allows_only_configured_frontend_origins(self):
        client=TestClient(create_app(self.runtime,start_runtime=False,allowed_origins=['https://davaoragcitizencharter.com']))
        headers={'Origin':'https://davaoragcitizencharter.com','Access-Control-Request-Method':'POST','Access-Control-Request-Headers':'content-type'}
        response=client.options('/api/query',headers=headers)
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.headers['access-control-allow-origin'],headers['Origin'])
        headers['Origin']='https://unrelated.example'
        response=client.options('/api/query',headers=headers)
        self.assertEqual(response.status_code,400)
        self.assertNotIn('access-control-allow-origin',response.headers)
        self.runtime.pipeline.handle_query.assert_not_called()

    def test_static_source_registry_matches_backend_sources(self):
        import json,hashlib
        from app.website import ROOT,SOURCE_NAMES
        registry=json.loads((ROOT/'config/website_sources.json').read_text())
        self.assertEqual({s['id']:(s['office'],s['filename']) for s in registry},SOURCE_NAMES)
        for s in registry:
            self.assertEqual(hashlib.sha256((ROOT/'data/raw_charters'/s['filename']).read_bytes()).hexdigest(),s['sha256'])

    def test_registered_profile_still_matches_frozen_inputs(self):
        candidate,hashes=registered_profile()
        self.assertEqual(candidate['k'],3);self.assertGreaterEqual(len(hashes),10)

    def test_payload_limits_and_no_diagnostic_exposure(self):
        for question in ['   ','x'*2001]:self.assertEqual(self.client.post('/api/query',json={'query':question}).status_code,422)
        r=self.client.post('/api/query',json={'query':'Synthetic website smoke check?'})
        self.assertEqual(r.status_code,200);self.assertEqual(r.json()['answer'],'Synthetic response [S1].')
        self.assertNotIn('diagnostics',r.json());self.assertEqual(r.headers['cache-control'],'no-store')

    def test_offline_and_single_request_capacity(self):
        self.runtime.health.return_value={'status':'model_offline','message':'Offline'}
        self.assertEqual(self.client.post('/api/query',json={'query':'Test'}).status_code,503)
        self.runtime.pipeline.handle_query.assert_not_called()
        self.runtime.health.return_value={'status':'ready','message':'Ready'}
        self.runtime.query_lock.acquire()
        try:
            r=self.client.post('/api/query',json={'query':'Test'});self.assertEqual(r.status_code,429);self.assertEqual(r.headers['retry-after'],'15')
        finally:self.runtime.query_lock.release()

    def test_failed_request_releases_lock(self):
        self.runtime.pipeline.handle_query.side_effect=RuntimeError('synthetic failure')
        with self.assertLogs('app.website',level='ERROR'):
            self.assertEqual(self.client.post('/api/query',json={'query':'Test'}).status_code,503)
        self.assertFalse(self.runtime.query_lock.locked())

    def test_language_selection_is_request_local_and_validated(self):
        from app.website_language import REQUESTED_LANGUAGE
        observed=[]
        def answer(question):
            observed.append((question,REQUESTED_LANGUAGE.get()))
            return {'status':'ANSWERED','answer':'Synthetic'}
        self.runtime.pipeline.handle_query.side_effect=answer
        for selection in ['bislish','taglish','auto']:
            self.assertEqual(self.client.post('/api/query',json={'query':'Original query','response_language':selection}).status_code,200)
        self.assertEqual(observed,[('Original query',s) for s in ['bislish','taglish','auto']])
        self.assertEqual(REQUESTED_LANGUAGE.get(),'auto')
        self.assertEqual(self.client.post('/api/query',json={'query':'Test','response_language':'invalid'}).status_code,422)

    def test_clarification_and_incomplete_answer_preserved(self):
        for status in ['CLARIFICATION_REQUIRED','GENERATION_INCOMPLETE','NO_SUPPORTED_ANSWER']:
            self.runtime.pipeline.handle_query.return_value={'status':status,'answer':'Original response','clarification_prompt':'Which service?'}
            data=self.client.post('/api/query',json={'query':'Test'}).json()
            self.assertEqual(data['status'],status);self.assertEqual(data['answer'],'Original response')

    def test_model_digest_mismatch_blocks_readiness(self):
        runtime=Runtime();runtime.pipeline=SimpleNamespace(endpoint='http://127.0.0.1:11434/api/generate',model_name='eboss-mistral',website_profile={'model_digest':'expected'})
        response=Mock();response.json.return_value={'models':[{'name':'eboss-mistral:latest','digest':'wrong'}]}
        with patch('app.website.requests.get',return_value=response):
            self.assertEqual(runtime.health()['status'],'model_mismatch')

    def test_readiness_log_uses_loaded_prompt_version(self):
        runtime=Runtime(factory=lambda:SimpleNamespace(website_profile={'website_prompt_version':'test-version'}))
        with self.assertLogs('app.website',level='INFO') as messages:
            runtime.load()
        self.assertIsNone(runtime.error)
        self.assertIn('test-version',messages.output[0])

    def test_citation_route_is_derived_from_source_identity(self):
        result=public_result({'status':'ANSWERED','citations':[{'citation':'S1','file_source':'BFP-CITIZENS-CHARTER-2022.pdf','pdf_relative_page':1,'text':'Synthetic excerpt.'},{'citation':'S2','file_source':'../secret','text':'Unknown source'}]})
        self.assertEqual(result['citations'][0]['source_url'],'/sources/fire.pdf#page=1')
        self.assertIsNone(result['citations'][1]['source_url'])


if __name__=='__main__':unittest.main()
