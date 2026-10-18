import unittest
from scripts.review_bfp_matrix import assign_dots


class MatrixTests(unittest.TestCase):
    def setUp(self):
        self.rows=[{'y_range':[0,10]},{'y_range':[10,20]}]
        self.cols=[{'x_range':[0,10]},{'x_range':[10,20]}]

    def test_sparse_cells(self):
        self.assertEqual(assign_dots([[12,2,14,4]],self.rows,self.cols),[[1],[]])

    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            assign_dots([[2,2,4,4],[3,3,5,5]],self.rows,self.cols)

    def test_boundary_rejected(self):
        with self.assertRaises(ValueError):
            assign_dots([[9,2,11,4]],self.rows,self.cols)

    def test_outside_rejected(self):
        with self.assertRaises(ValueError):
            assign_dots([[22,2,24,4]],self.rows,self.cols)


if __name__=='__main__':
    unittest.main()
