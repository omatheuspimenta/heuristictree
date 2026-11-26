import itertools
import random
from collections import Counter

import pytest

from heuristictree.tree import METHODS, Solution, _tree_pattern, tree, write_solution

REPRO = (
    1188,
    [51, 355, 236, 206, 226, 341, 215, 189, 431],
    [2, 3, 3, 2, 2, 2, 2, 1, 1],
)


def check_invariants(s: Solution, L: int, l: list[int], d: list[int], small=0):
    """Independent re-check of every invariant from the raw patterns."""
    demand: Counter[int] = Counter()
    for length, qty in zip(l, d, strict=True):
        demand[length] += qty
    demand = +demand
    threshold = small or (min(demand) if demand else 0)

    cut: Counter[int] = Counter()
    leftover = loss = bars = 0
    for p in s.patterns:
        assert p.count >= 1
        assert all(pieces >= 1 for _, pieces in p.cuts)  # x_i >= 0, no empty cuts
        used = sum(length * pieces for length, pieces in p.cuts)
        assert used <= L  # sum(x_i * l_i) <= L
        assert p.waste == L - used  # recorded L_hat is the real residual
        for length, pieces in p.cuts:
            cut[length] += pieces * p.count
        bars += p.count
        if p.waste < threshold:
            loss += p.waste * p.count
        else:
            leftover += p.waste * p.count

    assert cut == demand  # exact demand: no under- or over-cutting
    assert (s.bars, s.leftover, s.loss) == (bars, leftover, loss)
    items = sum(length * qty for length, qty in demand.items())
    assert s.leftover + s.loss + items == s.bars * L
    assert s.bars >= -(-items // L)  # never below the lower bound (Eq. 3)
    assert s.small_item == threshold


# --------------------------------------------------------------------------- #
# Reproducer from the issue
# --------------------------------------------------------------------------- #
def test_reproducer_corrected_tree():
    L, l, d = REPRO
    s = tree(L, l, d, method="tree")
    assert (s.bars, s.leftover, s.loss) == (4, 201, 80)
    assert len(s.patterns) == 4
    check_invariants(s, L, l, d)


def test_reproducer_best_is_at_least_as_good():
    L, l, d = REPRO
    s = tree(L, l, d)
    check_invariants(s, L, l, d)
    assert s.bars == 4 == s.lower_bound
    assert s.loss <= 80


def test_tree_pattern_adds_instead_of_overwriting():
    # In v1 this branch overwrote x[236] = 3 with 1 while still subtracting the
    # piece from the residual, recording a residual of 28 for a bar using 688.
    l = [431, 355, 341, 236, 226, 215, 51]
    d = [1, 2, 2, 3, 2, 1, 2]
    x = _tree_pattern(1188, l, d)
    assert sum(a * b for a, b in zip(x, l, strict=True)) == 1160
    assert all(0 <= xi <= di for xi, di in zip(x, d, strict=True))


def test_paper_example_and_bar_count():
    L, l, d = 100, [20, 30, 40, 50], [8, 6, 4, 2]
    for method in METHODS:
        s = tree(L, l, d, method=method)
        check_invariants(s, L, l, d)
        assert s.bars == 6  # v1 reported 7 for the same six patterns


# --------------------------------------------------------------------------- #
# Exhaustive and randomized invariant checks
# --------------------------------------------------------------------------- #
def score(s: Solution) -> tuple[int, int]:
    return s.bars, s.loss


def small_instances():
    for L in (5, 7, 10):
        for n in (1, 2, 3):
            for l in itertools.combinations(range(1, L + 1), n):
                for d in itertools.product(range(3), repeat=n):
                    yield L, list(l), list(d)


def test_exhaustive_small_instances():
    count = 0
    for L, l, d in small_instances():
        results = {m: tree(L, l, d, method=m, max_iterations=30) for m in METHODS}
        for s in results.values():
            check_invariants(s, L, l, d)
        assert score(results["best"]) <= score(results["tree"])
        assert score(results["best"]) <= score(results["maxfill"])
        count += 1
    assert count > 1000


@pytest.mark.parametrize("seed", range(4))
def test_random_instances(seed):
    rng = random.Random(seed)
    for _ in range(60):
        L = rng.choice([50, 100, 1188, rng.randint(2, 3000)])
        n = rng.randint(1, 25)
        l = [rng.randint(1, L) for _ in range(n)]
        d = [rng.choice([0, 1, 2, 3, rng.randint(4, 40)]) for _ in range(n)]
        small = rng.choice([0, 0, rng.randint(1, L)])
        # A small search budget is enough here: these tests check invariants.
        results = {
            m: tree(L, l, d, small, method=m, max_iterations=200) for m in METHODS
        }
        for s in results.values():
            check_invariants(s, L, l, d, small)
        assert score(results["best"]) <= score(results["tree"])
        assert score(results["best"]) <= score(results["maxfill"])


def test_benchmark_like_instance():
    rng = random.Random(7)
    l = [rng.randint(20, 444) for _ in range(300)]
    d = [rng.randint(4, 15) for _ in range(300)]
    s = tree(1188, l, d)
    check_invariants(s, 1188, l, d)
    assert s.bars <= s.lower_bound + 1


# --------------------------------------------------------------------------- #
# Edge cases and input handling
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("method", METHODS)
def test_item_equal_to_bar_length(method):
    s = tree(100, [100], [3], method=method)
    check_invariants(s, 100, [100], [3])
    assert (s.bars, s.leftover, s.loss) == (3, 0, 0)


@pytest.mark.parametrize("method", METHODS)
def test_single_item(method):
    s = tree(100, [60], [1], method=method)
    assert (s.bars, s.leftover, s.loss) == (1, 0, 40)  # 40 < 60: loss


@pytest.mark.parametrize("method", METHODS)
def test_zero_demands_are_ignored(method):
    s = tree(100, [50, 30, 10], [2, 0, 0], method=method)
    check_invariants(s, 100, [50, 30, 10], [2, 0, 0])
    assert s.small_item == 50  # smallest *demanded* item (v1 used 10)
    assert (s.bars, s.leftover, s.loss) == (1, 0, 0)


@pytest.mark.parametrize("d", [[], [0, 0]])
def test_no_demand(d):
    s = tree(100, [10, 20][: len(d)], d)
    assert (s.bars, s.leftover, s.loss, s.patterns) == (0, 0, 0, ())


def test_duplicate_lengths_are_merged():
    s = tree(100, [30, 30, 40], [1, 1, 1])
    assert s.demand == {40: 1, 30: 2}
    check_invariants(s, 100, [30, 30, 40], [1, 1, 1])


def test_custom_small_item():
    s = tree(100, [60], [1], 30)
    assert (s.leftover, s.loss) == (40, 0)  # 40 >= 30: leftover


def test_inputs_are_not_modified():
    l, d = [20, 50, 30, 50], [3, 1, 2, 1]
    tree(100, l, d)
    assert (l, d) == ([20, 50, 30, 50], [3, 1, 2, 1])


def test_deterministic():
    rng = random.Random(3)
    l = [rng.randint(20, 444) for _ in range(80)]
    d = [rng.randint(1, 15) for _ in range(80)]
    assert tree(1188, l, d) == tree(1188, l, d)


@pytest.mark.parametrize(
    "args",
    [
        (100, [120, 30], [1, 2]),  # item longer than the bar (v1: infinite loop)
        (100, [0, 30], [1, 1]),  # zero length (v1: ZeroDivisionError)
        (100, [30, 40], [-1, 2]),  # negative demand (v1: accepted silently)
        (100, [30], [1, 2]),  # size mismatch
        (0, [30], [1]),  # non-positive bar length
        (100, [30.5], [1]),  # non-integer length
        (100, [30], [True]),  # bool is not a demand
    ],
)
def test_invalid_input(args):
    with pytest.raises(ValueError):
        tree(*args)


def test_invalid_options():
    with pytest.raises(ValueError):
        tree(100, [30], [1], method="nope")
    with pytest.raises(ValueError):
        tree(100, [30], [1], -1)
    with pytest.raises(ValueError):
        tree(100, [30], [1], max_iterations=-1)


def test_item_longer_than_bar_with_zero_demand_is_ignored():
    s = tree(100, [120, 30], [0, 2])
    assert s.bars == 1


def test_validate_detects_corruption():
    s = tree(100, [30], [3])
    broken = Solution(
        bar_length=s.bar_length,
        small_item=s.small_item,
        patterns=s.patterns,
        method=s.method,
        lower_bound=s.lower_bound,
        demand={30: 4},
    )
    with pytest.raises(AssertionError):
        broken.validate()


def test_write_solution(tmp_path):
    out = tmp_path / "out.txt"
    s = tree(*REPRO, output_path=str(out))
    text = out.read_text()
    assert f"Bars: {s.bars} (lower bound {s.lower_bound})" in text
    assert f"Loss: {s.loss}" in text
    assert text.count("Pattern ") == len(s.patterns)
    write_solution(s, str(out))  # overwrites instead of appending
    assert out.read_text() == text
