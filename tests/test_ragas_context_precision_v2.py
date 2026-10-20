import unittest,json,math
from types import SimpleNamespace
from src.ragas_context_precision_v2 import GroundedContextPrecision
from ragas.metrics._context_precision import ContextPrecision

class FakeJudge:
    def __init__(self,outputs):self.outputs=iter(outputs);self.prompts=[]
    async def generate(self,prompt,**kwargs):
        self.prompts.append(prompt.to_string())
        return SimpleNamespace(generations=[[SimpleNamespace(text=next(self.outputs))]])

class RagasContextPrecisionV2Tests(unittest.IsolatedAsyncioTestCase):
    async def test_valid_results_use_actual_ragas_average_precision(self):
        outputs=[json.dumps({'reason':'supported','verdict':'1','evidence_quotes':['The fee is 12.']}),json.dumps({'reason':'unrelated','verdict':'0','evidence_quotes':[]})]
        llm=FakeJudge(outputs);metric=GroundedContextPrecision();metric.llm=llm
        row={'question':'What is the fee?','ground_truth':'The fee is 12.','contexts':['The fee is 12.','OFFICE HEADER']}
        score=await metric._ascore(row,[],True)
        self.assertEqual(score,ContextPrecision()._calculate_average_precision([{'verdict':'1'},{'verdict':'0'}]))
        self.assertEqual(len(llm.prompts),2)

    async def test_unverifiable_positive_is_missing_never_zero_or_one(self):
        llm=FakeJudge([json.dumps({'reason':'copied reference','verdict':'1','evidence_quotes':['The fee is 12.']})]);metric=GroundedContextPrecision();metric.llm=llm
        score=await metric._ascore({'question':'Fee?','ground_truth':'The fee is 12.','contexts':['OFFICE HEADER']},[],True)
        self.assertTrue(math.isnan(score))

    async def test_one_format_retry_is_audited(self):
        llm=FakeJudge(['{}',json.dumps({'reason':'supported','verdict':'1','evidence_quotes':['The fee is 12.']})]);metric=GroundedContextPrecision();metric.llm=llm;metric.format_retry_limit=1;events=[];metric.audit_sink=events.append
        score=await metric._ascore({'question':'Fee?','ground_truth':'The fee is 12.','contexts':['The fee is 12.']},[],True)
        self.assertAlmostEqual(score,1)
        self.assertEqual(len(llm.prompts),2)
        self.assertEqual(len(events),1)
        self.assertIn('Output-format retry only',llm.prompts[1])

    async def test_valid_wrong_verdict_is_not_retried(self):
        llm=FakeJudge([json.dumps({'reason':'absent','verdict':'0','evidence_quotes':[]})]);metric=GroundedContextPrecision();metric.llm=llm;metric.format_retry_limit=1
        score=await metric._ascore({'question':'Fee?','ground_truth':'The fee is 12.','contexts':['The fee is 12.']},[],True)
        self.assertEqual(score,0)
        self.assertEqual(len(llm.prompts),1)

if __name__=='__main__':unittest.main()
