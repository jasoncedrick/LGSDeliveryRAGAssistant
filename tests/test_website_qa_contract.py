"""Corrupt/partial QA archives must never masquerade as successful reruns."""
import copy
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

from scripts.website_qa_contract import (
    validate_cases, select_cases, validate_records, read_records, completion,
)


class QAContractTests(unittest.TestCase):
    def setUp(self):
        self.cases=[{'id':f'Q{i:03}', 'query':f'Synthetic query {i}', 'category':'synthetic',
                     'data':{'status':'ANSWERED'}} for i in range(1,201)]
        self.record={'id':'Q001','query':'Synthetic query 1','category':'synthetic',
                     'baseline':{'status':'ANSWERED'},'candidate':{'status':'ANSWERED'}}

    def test_full_input_unique_and_nonempty(self):
        self.assertEqual(len(validate_cases(self.cases)),200)
        for field,value in [('id','Q001'),('query','Synthetic query 1'),('query','')]:
            cases=copy.deepcopy(self.cases);cases[1][field]=value
            with self.assertRaises(ValueError):validate_cases(cases)
        with self.assertRaises(ValueError):validate_cases(self.cases[:-1])

    def test_selection_rejects_typos_and_duplicate_requests(self):
        for selection in ['Q001,Q001','Q001,','Q999']:
            with self.assertRaises(ValueError):select_cases(self.cases,selection)
        self.assertEqual([c['id'] for c in select_cases(self.cases,'Q002,Q001')],['Q001','Q002'])

    def test_resume_rejects_duplicate_mismatched_and_foreign_records(self):
        for field,value in [('id','Q999'),('query','different'),('category','changed'),
                            ('baseline',{}),('candidate',{})]:
            record=copy.deepcopy(self.record);record[field]=value
            with self.assertRaises(ValueError):validate_records([record],self.cases)
        with self.assertRaises(ValueError):validate_records([self.record,self.record],self.cases)
        with self.assertRaises(ValueError):validate_records([self.record],self.cases,require_complete=True)

    def test_truncated_record_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'records.jsonl'
            for raw in [json.dumps(self.record).encode(),b'{broken}\n',b'\n']:
                p.write_bytes(raw)
                with self.assertRaises(ValueError):read_records(p)
                self.assertEqual(p.read_bytes(),raw)
            p.write_text(json.dumps(self.record)+'\n')
            self.assertEqual(read_records(p),[self.record])

    def test_exception_is_not_a_clean_completion(self):
        record=copy.deepcopy(self.record);record['candidate']['status']='QA_EXCEPTION'
        report=completion([record],self.cases[:1])
        self.assertEqual(report['execution'],'COMPLETE_WITH_ERRORS')
        self.assertEqual(report['exception_ids'],['Q001'])
        self.assertEqual(report['answer_quality'],'NOT_CERTIFIED')

    def test_completed_resume_never_loads_model(self):
        from scripts import run_website_grounding_qa as runner
        (runner.ROOT/'tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=runner.ROOT/'tmp') as folder:
            archive=Path(folder)/'synthetic.zip'
            with zipfile.ZipFile(archive,'w') as z:
                z.writestr('eboss-200-repeat-20261028/results.json',json.dumps({'results':self.cases}))
            pipeline=Mock();pipeline.handle_query.return_value={'status':'ANSWERED'}
            pipeline.normalizer.last_trace=None
            runtime=Mock();runtime.model_state.return_value='ready'
            argv=['runner','--archive',str(archive),'--output',str(Path(folder)/'run'),'--ids','Q001']
            with patch('sys.argv',argv),patch.object(runner,'create_pipeline',return_value=pipeline) as factory,patch.object(runner,'Runtime',return_value=runtime):
                self.assertEqual(runner.main(),0)
                factory.assert_called_once()
                pipeline.handle_query.assert_called_once_with('Synthetic query 1')
                factory.reset_mock();pipeline.reset_mock()
                self.assertEqual(runner.main(),0)
                factory.assert_not_called();pipeline.handle_query.assert_not_called()
            self.assertEqual(len(read_records(Path(folder)/'run/results.jsonl')),1)


if __name__=='__main__':unittest.main()
