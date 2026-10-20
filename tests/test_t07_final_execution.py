import ast
from pathlib import Path
import unittest
from scripts.build_t07_final_scorer import adapted
from scripts.export_t07_final_metrics import mean


class FinalExecutionTests(unittest.TestCase):
    def test_scorer_adapter_is_reproducible_and_original_unchanged(self):
        root = Path(__file__).resolve().parents[1]
        original = (root / 'scripts/score_development_ragas.py').read_text(encoding='utf-8')
        actual = (root / 'scripts/score_final_ragas.py').read_text(encoding='utf-8')
        self.assertEqual(adapted(original), actual)
        ast.parse(actual)
        self.assertIn("Only development archives accepted", original)
        self.assertIn('validate_final_source(source, protocol, args)', actual)

    def test_missing_gold_and_judge_failures_are_not_zero(self):
        self.assertEqual(mean([None, 0.0, 1.0]), (0.5, 2))
        self.assertEqual(mean([None]), (None, 0))


if __name__ == '__main__':
    unittest.main()
