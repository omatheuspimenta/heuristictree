"""Solution quality: exact optima on tiny instances and v1 regression."""

import itertools
import random
import tarfile
from functools import cache
from pathlib import Path

import pytest

from heuristictree.parser import parse_instance
from heuristictree.tree import METHODS, tree

DATA = Path(__file__).resolve().parent.parent / "data" / "execution"

# (bars, loss) of v1.0.3 on benchmark instances, recomputed from its patterns.
V1_RESULTS = {
    "1/class_1.dat.tar.gz": (16, 16),
    "1/class_7.dat.tar.gz": (36, 52),
    "1/class_13.dat.tar.gz": (10, 20),
    "1/class_29.dat.tar.gz": (35, 57),
    "1/class_42.dat.tar.gz": (11, 22),
    "1/class_58.dat.tar.gz": (25, 41),
    "1/class_64.dat.tar.gz": (37, 13),
    "1/class_77.dat.tar.gz": (37, 36),
    "1/class_85.dat.tar.gz": (4, 8),
    "1/class_99.dat.tar.gz": (38, 48),
    "2/class_1.dat.tar.gz": (130, 350),
    "2/class_7.dat.tar.gz": (171, 320),
    "2/class_13.dat.tar.gz": (138, 349),
    "2/class_29.dat.tar.gz": (102, 174),
    "2/class_42.dat.tar.gz": (49, 293),
    "2/class_58.dat.tar.gz": (48, 512),
    "2/class_64.dat.tar.gz": (134, 383),
    "2/class_77.dat.tar.gz": (53, 153),
    "2/class_85.dat.tar.gz": (87, 290),
    "2/class_99.dat.tar.gz": (28, 57),
    "3/class_1.dat.tar.gz": (55, 26),
    "3/class_7.dat.tar.gz": (53, 10),
    "3/class_13.dat.tar.gz": (48, 33),
    "3/class_29.dat.tar.gz": (69, 45),
    "3/class_42.dat.tar.gz": (42, 34),
    "3/class_58.dat.tar.gz": (48, 10),
    "3/class_64.dat.tar.gz": (52, 19),
    "3/class_77.dat.tar.gz": (46, 26),
    "3/class_85.dat.tar.gz": (64, 22),
    "3/class_99.dat.tar.gz": (44, 7),
}


def exact_optimum(L, l, d, small=0):
    """Exact lexicographic (bars, loss) minimum by search over pattern sets."""
    merged: dict[int, int] = {}
    for length, qty in zip(l, d, strict=True):
        if qty:
            merged[length] = merged.get(length, 0) + qty
    lengths = sorted(merged, reverse=True)
    demand = tuple(merged[x] for x in lengths)
    threshold = small or (lengths[-1] if lengths else 0)
    patterns = []
    for p in itertools.product(
        *(range(min(q, L // ln) + 1) for ln, q in zip(lengths, demand, strict=True))
    ):
        used = sum(a * b for a, b in zip(p, lengths, strict=True))
        if any(p) and used <= L:
            waste = L - used
            patterns.append((p, waste if waste < threshold else 0))

    @cache
    def solve(rem):
        if not any(rem):
            return (0, 0)
        best = None
        for p, loss in patterns:
            if all(a <= b for a, b in zip(p, rem, strict=True)):
                bars, sub_loss = solve(
                    tuple(b - a for a, b in zip(p, rem, strict=True))
                )
                candidate = (bars + 1, sub_loss + loss)
                if best is None or candidate < best:
                    best = candidate
        return best

    return solve(demand)


def tiny_instances(count, seed):
    rng = random.Random(seed)
    for _ in range(count):
        L = rng.choice([20, 50, 100, rng.randint(10, 200)])
        n = rng.randint(1, 4)
        l = [rng.randint(max(1, L // 10), L) for _ in range(n)]
        d = [rng.randint(0, 4) for _ in range(n)]
        yield L, l, d


def test_exact_optimum_helper():
    assert exact_optimum(100, [20, 30, 40, 50], [8, 6, 4, 2]) == (6, 0)
    assert exact_optimum(20, [9, 3], [4, 4]) == (3, 2)
    assert exact_optimum(100, [60], [1]) == (1, 40)


def test_best_matches_exact_optimum_on_tiny_instances():
    misses = []
    total = 0
    for L, l, d in tiny_instances(250, seed=0):
        optimum = exact_optimum(L, l, d)
        results = {m: tree(L, l, d, method=m) for m in METHODS}
        for method, s in results.items():
            assert (s.bars, s.loss) >= optimum, (method, L, l, d)
        if (results["best"].bars, results["best"].loss) != optimum:
            misses.append((L, l, d))
        total += 1
    # The heuristic is not exact, but it should almost always reach the optimum.
    assert len(misses) <= total // 100, misses


def test_best_fixes_known_former_misses():
    # Instances on which earlier versions of the local search were suboptimal.
    assert (tree(20, [9, 3], [4, 4]).loss) == 2
    s = tree(80, [53, 18, 49, 22], [3, 4, 2, 1])
    assert (s.bars, s.loss) == exact_optimum(80, [53, 18, 49, 22], [3, 4, 2, 1])


def load(name):
    with tarfile.open(DATA / name) as archive:
        member = next(m for m in archive.getmembers() if m.isfile())
        handle = archive.extractfile(member)
        assert handle is not None
        return parse_instance(handle.read().decode(), name)


@pytest.mark.parametrize("name", sorted(V1_RESULTS))
def test_never_worse_than_v1_on_benchmark(name):
    L, l, d = load(name)
    s = tree(L, l, d)
    s.validate()
    assert (s.bars, s.loss) <= V1_RESULTS[name]
    assert s.bars <= V1_RESULTS[name][0]
