import unittest,math
from src.context_precision_judge_v2 import build_prompt,context_precision_from_valid_verdicts
class ContextPrecisionJudgeV2Tests(unittest.TestCase):
 def test_reference_is_separate_from_last_evidence_block(self):
  p=build_prompt('What is the fee?','The fee is PHP500.','OFFICE HEADER')
  actual=p.split('Now evaluate only the following actual item.')[1]
  self.assertLess(actual.index('The fee is PHP500.'),actual.index('OFFICE HEADER'))
  self.assertIn('RETRIEVED_CONTEXT_JSON_ONLY_EVIDENCE:\n"OFFICE HEADER"',actual)
 def test_source_template_tokens_are_not_interpreted(self):
  p=build_prompt('__CONTEXT__','reference','source')
  self.assertIn('"__CONTEXT__"',p)
 def test_ordered_precision_and_missing_outputs(self):
  self.assertAlmostEqual(context_precision_from_valid_verdicts(['1','0','1']), (1+2/3)/(2+1e-10))
  self.assertEqual(context_precision_from_valid_verdicts(['0','0']),0)
  self.assertTrue(math.isnan(context_precision_from_valid_verdicts(['1',None])))
if __name__=='__main__':unittest.main()
