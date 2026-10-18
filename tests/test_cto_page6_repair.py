import unittest
from scripts.repair_cto_page6 import pair_fee_lines


def line(text,y):
    return {'text':text,'bbox':[0,y,100,y+10]}


class FeeAlignmentTests(unittest.TestCase):
    def test_coordinates_determine_pairing(self):
        result=pair_fee_lines([line('Carabaos/Buffaloes',10),line('Poultry',30)],
                              [line('1.00',30),line('70.00',10)])
        self.assertEqual([p['fee']['text'] for p in result],['70.00','1.00'])

    def test_missing_fee_rejected(self):
        with self.assertRaises(ValueError):
            pair_fee_lines([line('Poultry',10)],[])

    def test_shifted_fee_rejected(self):
        with self.assertRaises(ValueError):
            pair_fee_lines([line('Poultry',10)],[line('1.00',30)])

    def test_ambiguous_fee_rejected(self):
        with self.assertRaises(ValueError):
            pair_fee_lines([line('a',10),line('b',30)],
                           [line('50.00',10),line('50.00',10.5)])


if __name__=='__main__':
    unittest.main()
