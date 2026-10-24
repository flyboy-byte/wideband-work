import unittest
import math
from layout_metrics import cells, uncovered_component


class MetricsTest(unittest.TestCase):
    def test_lengths(self):
        for end in ((.01, 0), (1, 0), (3, 4)):
            parts = cells((0, 0), end, .25)
            self.assertAlmostEqual(sum(p[3] for p in parts), math.dist((0, 0), end))
            self.assertTrue(all(p[3] <= .25 for p in parts))
        self.assertEqual(cells((0, 0), (0, 0), .25), [])

    def test_join_order_direction(self):
        edges = [((0, 0), (1, 0), 1), ((1, 0), (2, 0), 1), ((10, 0), (10.5, 0), .5)]
        for variant in (edges, edges[::-1], [(b, a, w) for a, b, w in edges]):
            self.assertEqual(uncovered_component(variant), 2)

    def test_branch_and_covered_break(self):
        self.assertEqual(uncovered_component([((0, 0), (1, 0), 1), ((1, 0), (1, 1), 1),
                                             ((1, 0), (2, 0), 1)]), 3)
        self.assertEqual(uncovered_component([((0, 0), (1, 0), 1), ((2, 0), (3, 0), 1)]), 1)
        self.assertEqual(uncovered_component([]), 0)


if __name__ == '__main__':
    unittest.main()
