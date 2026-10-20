import unittest
from scripts.rescore_t07_grids_v2 import aggregate


class Metric:
    def _calculate_average_precision(self, values):
        total = count = 0
        for rank, value in enumerate(values, 1):
            if value['verdict'] == '1':
                count += 1
                total += count / rank
        return total / (count + 1e-10)


class PairedGridTests(unittest.TestCase):
    def fixture(self):
        records = {str(i): dict(pillar=str(i // 18), language=str((i // 6) % 3)) for i in range(90)}
        rows = [dict(grid_id=g, weights=[1, 0, 0], record_id=str(i),
                     rankings={'3': ['one'], '5': ['one']}) for g in range(17) for i in range(90)]
        verdicts = {(str(i), 'one'): {'verdict': '1'} for i in range(90)}
        return records, rows, verdicts

    def test_equal_cell_macro_and_all_conditions(self):
        records, rows, verdicts = self.fixture()
        result = aggregate(rows, records, verdicts, Metric())
        self.assertEqual(len(result), 34)
        self.assertAlmostEqual(result[0]['J'], 1)
        self.assertEqual(len(result[0]['cell_means']), 15)

    def test_missing_judgment_blocks_objective(self):
        records, rows, verdicts = self.fixture()
        verdicts[('0', 'one')] = None
        result = aggregate(rows, records, verdicts, Metric())
        self.assertIsNone(result[0]['J'])
        self.assertEqual(result[0]['failed_record_ids'], ['0'])

    def test_stopped_query_zero_retained_in_denominator(self):
        records, rows, verdicts = self.fixture()
        for row in rows:
            if row['record_id'] == '0':
                row['rankings'] = {'3': [], '5': []}
        result = aggregate(rows, records, verdicts, Metric())
        self.assertAlmostEqual(result[0]['J'], 89 / 90)
        self.assertEqual(result[0]['failed_record_ids'], [])


if __name__ == '__main__':
    unittest.main()
