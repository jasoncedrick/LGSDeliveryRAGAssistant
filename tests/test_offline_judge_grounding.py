import unittest,json
from src.offline_judge_grounding import parse_grounded_verdict
class OfflineJudgeEvidenceTests(unittest.TestCase):
 def test_reference_fact_cannot_be_used_as_context_quote(self):
  raw=json.dumps({'reason':'fee','verdict':'1','evidence_quotes':['PHP500']})
  self.assertEqual(parse_grounded_verdict(raw,'Office provides report forms.')[1],'QUOTE_NOT_IN_CONTEXT')
 def test_whitespace_differences_do_not_invalidate_real_quote(self):
  raw=json.dumps({'reason':'fee','verdict':'1','evidence_quotes':['FSIF = 15%']})
  self.assertIsNone(parse_grounded_verdict(raw,'FSIF =\n15%')[1])
 def test_negative_and_invalid_are_distinct(self):
  valid=json.dumps({'reason':'absent','verdict':'0','evidence_quotes':[]})
  self.assertEqual(parse_grounded_verdict(valid,'Title')[0]['verdict'],'0')
  self.assertEqual(parse_grounded_verdict('{}','Title')[1],'INVALID_SCHEMA')
 def test_positive_requires_evidence(self):
  raw=json.dumps({'reason':'present','verdict':'1','evidence_quotes':[]})
  self.assertEqual(parse_grounded_verdict(raw,'Title')[1],'MISSING_POSITIVE_EVIDENCE')
if __name__=='__main__':unittest.main()
