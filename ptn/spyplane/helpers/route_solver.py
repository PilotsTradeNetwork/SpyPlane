"""One-way TSP path through 3D points (open path, free start and end)."""

import math
import random

NO_NODE = -1  # sentinel for "past either end of the path"


def distance_matrix(points):
    n = len(points)
    dist = [[0.0] * n for _ in range(n)]
    for i in range(n):
        point_i = points[i]
        row = dist[i]
        for j in range(i + 1, n):
            d = math.dist(point_i, points[j])
            row[j] = d
            dist[j][i] = d
    return dist


def path_length(path, dist):
    return sum(dist[path[k]][path[k + 1]] for k in range(len(path) - 1))


def nearest_neighbor(dist, n, start):
    unvisited = set(range(n))
    unvisited.remove(start)
    path = [start]
    current = start
    while unvisited:
        dist_from_current = dist[current]
        current = min(unvisited, key=dist_from_current.__getitem__)
        unvisited.remove(current)
        path.append(current)
    return path


def two_opt_path(path, dist):
    """
    2-opt for an OPEN path. Reversing path[i..j] replaces edges
    (before, first) + (last, after) with (before, last) + (first, after).
    At either end there is no edge to remove, which lets the endpoints move too.
    For each i, the best j is applied.
    """
    n = len(path)
    improved = True
    while improved:
        improved = False
        for i in range(n - 1):
            first = path[i]
            dist_from_first = dist[first]
            if i > 0:
                before = path[i - 1]
                dist_from_before = dist[before]
                old_left = dist_from_before[first]
            else:
                dist_from_before = None
                old_left = 0.0
            best_delta, best_j = -1e-12, -1
            for j in range(i + 1, n):
                if i == 0 and j == n - 1:
                    continue  # reversing the whole path changes nothing
                last = path[j]
                if j < n - 1:
                    after = path[j + 1]
                    old_right, new_right = dist[last][after], dist_from_first[after]
                else:
                    old_right = new_right = 0.0
                new_left = dist_from_before[last] if dist_from_before is not None else 0.0
                delta = new_left + new_right - old_left - old_right
                if delta < best_delta:
                    best_delta, best_j = delta, j
            if best_j >= 0:
                path[i : best_j + 1] = path[i : best_j + 1][::-1]
                improved = True
    return path


def or_opt_path(path, dist, max_seg=3):
    """
    Move a chunk of 1-3 consecutive points to a better spot in the path
    (optionally flipped). Catches improvements 2-opt alone misses.
    """
    n = len(path)

    def edge(x, y):
        return dist[x][y] if x != NO_NODE and y != NO_NODE else 0.0

    improved_any = False
    improved = True
    while improved:
        improved = False
        for seg_len in range(1, max_seg + 1):
            for i in range(n - seg_len + 1):
                segment = path[i : i + seg_len]
                prev_node = path[i - 1] if i > 0 else NO_NODE
                next_node = path[i + seg_len] if i + seg_len < n else NO_NODE
                # Saved by cutting the segment out and joining its neighbours
                removal_gain = edge(prev_node, segment[0]) + edge(segment[-1], next_node) - edge(prev_node, next_node)
                if removal_gain <= 1e-12:
                    continue
                rest = path[:i] + path[i + seg_len :]
                best_gain, best_pos, best_segment = 1e-12, -1, None
                for pos in range(len(rest) + 1):  # insert before rest[pos]
                    if pos == i:
                        continue  # original position
                    left = rest[pos - 1] if pos > 0 else NO_NODE
                    right = rest[pos] if pos < len(rest) else NO_NODE
                    gap_edge = edge(left, right)
                    for oriented in (segment, segment[::-1]):
                        insert_cost = edge(left, oriented[0]) + edge(oriented[-1], right) - gap_edge
                        gain = removal_gain - insert_cost
                        if gain > best_gain:
                            best_gain, best_pos, best_segment = gain, pos, oriented
                if best_pos >= 0:
                    path[:] = rest[:best_pos] + best_segment + rest[best_pos:]
                    improved = improved_any = True
                    break
            if improved:
                break
    return path, improved_any


def improve(path, dist):
    """Alternate 2-opt and Or-opt until neither finds anything."""
    while True:
        path = two_opt_path(path, dist)
        path, changed = or_opt_path(path, dist)
        if not changed:
            return path


def default_starts(n):
    """Try every start for small inputs; scale back gently for large ones."""
    if n <= 60:
        return n
    return max(20, int(3 * math.sqrt(n)))


def solve_path(points, n_starts=None, seed=0):
    """
    One-way route through all points (free start and end).
    points: list of [x, y, z]. Returns (path indices, length).
    """
    n = len(points)
    if n <= 1:
        return list(range(n)), 0.0
    dist = distance_matrix(points)
    if n_starts is None:
        n_starts = default_starts(n)
    starts = random.Random(seed).sample(range(n), min(n_starts, n))  # noqa: S311 - not crypto

    best_path: list[int] = []
    best_len = math.inf
    for start in starts:
        path = improve(nearest_neighbor(dist, n, start), dist)
        length = path_length(path, dist)
        if length < best_len:
            best_path, best_len = path, length
    return best_path, best_len
