import itertools
import random

import pytest

from heuristictree.knapsack import max_fill
from heuristictree.parser import load_file, parse_instance


def brute_force(lengths, bounds, capacity):
    return max(
        fill
        for xs in itertools.product(*(range(b + 1) for b in bounds))
        if (fill := sum(x * ln for x, ln in zip(xs, lengths, strict=True))) <= capacity
    )


def test_max_fill_is_exact():
    rng = random.Random(0)
    for _ in range(2000):
        n = rng.randint(1, 5)
        lengths = sorted((rng.randint(1, 30) for _ in range(n)), reverse=True)
        bounds = [rng.randint(0, 4) for _ in range(n)]
        capacity = rng.randint(0, 80)
        x = max_fill(lengths, bounds, capacity)
        assert all(0 <= xi <= b for xi, b in zip(x, bounds, strict=True))
        fill = sum(xi * ln for xi, ln in zip(x, lengths, strict=True))
        assert fill == brute_force(lengths, bounds, capacity)


def test_max_fill_prefers_large_items():
    assert max_fill([60, 40, 20], [1, 1, 3], 100) == [1, 1, 0]


def test_max_fill_rejects_bad_input():
    with pytest.raises(ValueError):
        max_fill([1, 2], [1], 5)
    with pytest.raises(ValueError):
        max_fill([1], [1], -1)
    with pytest.raises(ValueError):
        max_fill([0], [1], 5)
    with pytest.raises(ValueError):
        max_fill([1], [-1], 5)


def test_load_simple_file(tmp_path):
    path = tmp_path / "inst.txt"
    path.write_text("1188\n229\t2\n\n208 1\n")
    assert load_file(path) == (1188, [229, 208], [2, 1])


def test_load_benchmark_file(tmp_path):
    path = tmp_path / "class_1.dat"
    path.write_text("!****\n!header\n\nL:1188\nn:2\nl: 229 208\nd: 2 1\n")
    assert load_file(str(path)) == (1188, [229, 208], [2, 1])


@pytest.mark.parametrize(
    "text",
    [
        "",
        "!only comments\n",
        "100 5\n20 1\n",
        "100\n20\n",
        "100\n20 x\n",
        "L:100\nl: 20 30\n",
        "L:100 200\nl: 20\nd: 1\n",
        "L:100\nl: 20 30\nd: 1\n",
        "L:100\nl 20\nd: 1\n",
    ],
)
def test_parse_errors(text):
    with pytest.raises(ValueError):
        parse_instance(text)
