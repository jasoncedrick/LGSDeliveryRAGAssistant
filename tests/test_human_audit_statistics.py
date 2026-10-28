import sys
from pathlib import Path
import itertools
import unittest
import numpy as np
from scipy import stats
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from analyze_human_audit import alpha, ordinal_manual, exact_wilcoxon

class StatisticsTests(unittest.TestCase):
    def test_ordinal_coincidences(self):
        rng=np.random.default_rng(91)
        for maximum in [4,5]:
            for _ in range(20):
                matrix=rng.integers(1,maximum+1,(3,25))
                self.assertAlmostEqual(alpha(matrix,maximum),ordinal_manual(matrix,maximum),12)
        self.assertEqual(alpha(np.array([[1,2,3]]*3),4),1)

    def test_exact_ties_and_zero_differences(self):
        for differences in [[0,0,0],[1,2,3],[-1,1,2,-2,0],[2,-2,2,0,-3,4]]:
            x=np.array(differences);x=x[x!=0]
            if len(x):
                ranks=stats.rankdata(abs(x));observed=abs(np.dot(ranks,np.sign(x)))
                p=np.mean([abs(np.dot(ranks,s))>=observed-1e-12 for s in itertools.product([-1,1],repeat=len(x))])
            else:p=1
            self.assertAlmostEqual(exact_wilcoxon(differences)['p_value'],p,12)

if __name__=='__main__':unittest.main()
