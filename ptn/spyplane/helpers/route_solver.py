"""One-way TSP path through 3D points (open path, free start and end)."""

import math
import random


def distance_matrix(points):
    n = len(points)
    dist = [[0.0] * n for _ in range(n)]
    for i in range(n):
        pi = points[i]
        row = dist[i]
        for j in range(i + 1, n):
            d = math.dist(pi, points[j])
            row[j] = d
            dist[j][i] = d
    return dist


def path_length(path, dist):
    return sum(dist[path[k]][path[k + 1]] for k in range(len(path) - 1))


def nearest_neighbor(dist, n, start):
    unvisited = set(range(n))
    unvisited.remove(start)
    path = [start]
    cur = start
    while unvisited:
        row = dist[cur]
        cur = min(unvisited, key=row.__getitem__)
        unvisited.remove(cur)
        path.append(cur)
    return path


def two_opt_path(path, dist):
    """
    2-opt for an OPEN path. Reversing path[i..j] replaces edges
    (i-1, i) and (j, j+1); at either end there is no edge to remove,
    which lets the endpoints move too. For each i, the best j is applied.
    """
    n = len(path)
    improved = True
    while improved:
        improved = False
        for i in range(n - 1):
            a = path[i - 1] if i > 0 else -1
            b = path[i]
            d_b = dist[b]
            ab = dist[a][b] if a >= 0 else 0.0
            d_a = dist[a] if a >= 0 else None
            best_delta, best_j = -1e-12, -1
            for j in range(i + 1, n):
                if i == 0 and j == n - 1:
                    continue  # reversing the whole path changes nothing
                c = path[j]
                if j < n - 1:
                    d = path[j + 1]
                    cd, bd = dist[c][d], d_b[d]
                else:
                    cd = bd = 0.0
                ac = d_a[c] if d_a is not None else 0.0
                delta = ac + bd - ab - cd
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
        return dist[x][y] if x >= 0 and y >= 0 else 0.0

    improved_any = False
    improved = True
    while improved:
        improved = False
        for seg_len in range(1, max_seg + 1):
            for i in range(n - seg_len + 1):
                seg = path[i : i + seg_len]
                p = path[i - 1] if i > 0 else -1
                q = path[i + seg_len] if i + seg_len < n else -1
                remove_gain = edge(p, seg[0]) + edge(seg[-1], q) - edge(p, q)
                if remove_gain <= 1e-12:
                    continue
                rest = path[:i] + path[i + seg_len :]
                best, best_k, best_seg = 1e-12, -1, None
                for k in range(len(rest) + 1):  # insert before rest[k]
                    if k == i:
                        continue  # original position
                    x = rest[k - 1] if k > 0 else -1
                    y = rest[k] if k < len(rest) else -1
                    base = edge(x, y)
                    for s in (seg, seg[::-1]):
                        gain = remove_gain - (edge(x, s[0]) + edge(s[-1], y) - base)
                        if gain > best:
                            best, best_k, best_seg = gain, k, s
                if best_k >= 0:
                    path[:] = rest[:best_k] + best_seg + rest[best_k:]
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
    for s in starts:
        path = improve(nearest_neighbor(dist, n, s), dist)
        length = path_length(path, dist)
        if length < best_len:
            best_path, best_len = path, length
    return best_path, best_len
