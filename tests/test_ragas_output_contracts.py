import copy
import unittest
from types import SimpleNamespace as NS
from src.ragas_output_contracts import apply_contracts


class Contracts(unittest.TestCase):
    def test_original_criteria_and_other_metrics_preserved(self):
        original = {'context_precision': NS(context_precision_prompt=NS(instruction='original precision')),
                    'answer_relevancy': NS(question_generation=NS(instruction='original relevance')),
                    'faithfulness': NS(instruction='original faithfulness')}
        candidate = copy.deepcopy(original)
        meta = apply_contracts(candidate)
        self.assertEqual(original['context_precision'].context_precision_prompt.instruction, 'original precision')
        self.assertTrue(candidate['context_precision'].context_precision_prompt.instruction.startswith('original precision\n'))
        self.assertTrue(candidate['answer_relevancy'].question_generation.instruction.startswith('original relevance\n'))
        self.assertEqual(candidate['faithfulness'].instruction, 'original faithfulness')
        self.assertEqual(meta['version'], 'ragas-output-contract-v1')

    def test_contract_has_required_shape_and_types(self):
        from src.ragas_output_contracts import INSTRUCTIONS
        self.assertIn('the string "0" or "1"', INSTRUCTIONS['context_precision'])
        self.assertIn('Use the key question, not answer', INSTRUCTIONS['answer_relevancy'])
        self.assertIn('the integer 0 or 1', INSTRUCTIONS['answer_relevancy'])


if __name__ == '__main__':
    unittest.main()
