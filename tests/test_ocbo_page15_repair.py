import unittest
from scripts.repair_ocbo_page15 import pair_spans


def line(text, y):
    return {'text':text,'bbox':[0,y,100,y+10]}


class SpanAlignmentTests(unittest.TestCase):
    def test_time_on_wrapped_line(self):
        pairs=pair_spans([[line('4.4 Evaluate plans',10),line('documents',22)]],
                         [line('1 Day',22)])
        self.assertEqual(pairs[0]['action'],'4.4 Evaluate plans documents')
        self.assertEqual(pairs[0]['processing_time'],'1 Day')

    def test_gap_is_not_nearest_neighbor_match(self):
        with self.assertRaises(ValueError):
            pair_spans([[line('4.4 Evaluate plans documents',10)]],[line('1 Day',40)])

    def test_multiple_times_in_span_rejected(self):
        with self.assertRaises(ValueError):
            pair_spans([[line('a',10),line('b',30)],[line('c',60)]],
                       [line('1 Day',10),line('4 Hours',30)])

    def test_missing_time_rejected(self):
        with self.assertRaises(ValueError):
            pair_spans([[line('a',10)]],[])


if __name__=='__main__':
    unittest.main()
