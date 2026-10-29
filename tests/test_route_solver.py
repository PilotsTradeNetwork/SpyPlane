import itertools
import math
import random
import unittest

from ptn.spyplane.helpers.route_solver import solve_path


class SolvePathTests(unittest.TestCase):
    def test_trivial_inputs(self):
        self.assertEqual(solve_path([]), ([], 0.0))
        self.assertEqual(solve_path([(1, 2, 3)]), ([0], 0.0))
        path, length = solve_path([(0, 0, 0), (3, 4, 0)])
        self.assertEqual(sorted(path), [0, 1])
        self.assertAlmostEqual(length, 5.0)

    def test_shuffled_line_is_walked_end_to_end(self):
        xs = list(range(0, 100, 10))
        random.Random(42).shuffle(xs)  # noqa: S311 - not crypto
        points = [(x, 0, 0) for x in xs]

        path, length = solve_path(points)

        walked = [points[i][0] for i in path]
        self.assertIn(walked, (sorted(xs), sorted(xs, reverse=True)))
        self.assertAlmostEqual(length, 90.0)

    def test_rectangle_avoids_long_side_twice(self):
        # Corners of a 10x1 rectangle: best open path is short-long-short = 12
        points = [(0, 0, 0), (10, 1, 0), (0, 1, 0), (10, 0, 0)]

        path, length = solve_path(points)

        self.assertAlmostEqual(length, 12.0)
        self.assertEqual(sorted(path), [0, 1, 2, 3])

    def test_3d_grid_snake(self):
        # 3x3x3 unit grid: an optimal open path visits every point with unit steps (26 edges)
        points = [(x, y, z) for x in range(3) for y in range(3) for z in range(3)]
        random.Random(7).shuffle(points)  # noqa: S311 - not crypto

        path, length = solve_path(points)

        self.assertEqual(sorted(path), list(range(len(points))))
        self.assertAlmostEqual(length, 26.0)
        for a, b in itertools.pairwise(path):
            self.assertAlmostEqual(math.dist(points[a], points[b]), 1.0)


if __name__ == "__main__":
    unittest.main()
