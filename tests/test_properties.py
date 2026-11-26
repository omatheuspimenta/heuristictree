"""Property-based tests (Hypothesis)."""

import dataclasses
import tomllib
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from heuristictree import __version__
from heuristictree.knapsack import max_fill
from heuristictree.parser import parse_instance
from heuristictree.tree import METHODS, Pattern, _tree_pattern, tree, write_solution

FAST = settings(max_examples=150, deadline=None)


@st.composite
def instances(draw, max_items=12):
    L = draw(st.integers(1, 2000))
    n = draw(st.integers(0, max_items))
    l = draw(st.lists(st.integers(1, L), min_size=n, max_size=n))
    d = draw(st.lists(st.integers(0, 20), min_size=n, max_size=n))
    small = draw(st.one_of(st.just(0), st.integers(1, L)))
    return L, l, d, small


@FAST
@given(instances(), st.sampled_from(METHODS))
def test_solution_invariants(instance, method):
    L, l, d, small = instance
    s = tree(L, l, d, small, method=method, max_iterations=100)
    s.validate()
    demand = {}
    for length, qty in zip(l, d, strict=True):
        if qty:
            demand[length] = demand.get(length, 0) + qty
    assert s.cut_items() == demand
    items = sum(k * v for k, v in demand.items())
    assert s.leftover + s.loss + items == s.bars * L
    threshold = small or (min(demand) if demand else 0)
    assert all(p.waste == L - p.used for p in s.patterns)
    assert s.loss == sum(p.waste * p.count for p in s.patterns if p.waste < threshold)


@FAST
@given(instances(max_items=8))
def test_best_never_worse_than_components(instance):
    L, l, d, small = instance
    best = tree(L, l, d, small, max_iterations=100)
    for method in ("tree", "maxfill"):
        other = tree(L, l, d, small, method=method)
        assert (best.bars, best.loss) <= (other.bars, other.loss)


@FAST
@given(instances(max_items=8), st.integers(0, 5))
def test_seeds_change_search_not_validity(instance, seed):
    L, l, d, small = instance
    s = tree(L, l, d, small, seed=seed, max_iterations=50)
    s.validate()
    assert s == tree(L, l, d, small, seed=seed, max_iterations=50)


@FAST
@given(instances())
def test_inputs_are_left_untouched(instance):
    L, l, d, small = instance
    l_copy, d_copy = list(l), list(d)
    tree(L, l, d, small, max_iterations=20)
    assert (l, d) == (l_copy, d_copy)


@FAST
@given(
    st.lists(st.tuples(st.integers(1, 50), st.integers(0, 6)), min_size=1, max_size=6),
    st.integers(0, 150),
    st.integers(0, 40),
)
def test_max_fill_properties(items, capacity, min_leftover):
    lengths = [a for a, _ in items]
    bounds = [b for _, b in items]
    plain = max_fill(lengths, bounds, capacity)
    aware = max_fill(lengths, bounds, capacity, min_leftover)
    for x in (plain, aware):
        assert all(0 <= xi <= b for xi, b in zip(x, bounds, strict=True))
        assert sum(xi * ln for xi, ln in zip(x, lengths, strict=True)) <= capacity
    fill = sum(xi * ln for xi, ln in zip(plain, lengths, strict=True))
    fill_aware = sum(xi * ln for xi, ln in zip(aware, lengths, strict=True))
    assert fill_aware <= fill
    waste = capacity - fill_aware
    if fill_aware != fill:  # loss-aware moved away from the maximum fill...
        assert waste >= min_leftover  # ...only to leave a usable leftover
        assert fill_aware > 0


@FAST
@given(
    st.integers(50, 1500).flatmap(
        lambda L: st.tuples(
            st.just(L),
            st.lists(st.integers(1, L), min_size=1, max_size=10, unique=True),
        )
    ),
    st.data(),
)
def test_tree_pattern_respects_demand_and_length(case, data):
    L, raw = case
    l = sorted(raw, reverse=True)
    d = data.draw(st.lists(st.integers(1, 10), min_size=len(l), max_size=len(l)))
    x = _tree_pattern(L, l, d)
    assert all(0 <= xi <= di for xi, di in zip(x, d, strict=True))
    assert 0 < sum(xi * li for xi, li in zip(x, l, strict=True)) <= L


@FAST
@given(instances(), st.booleans())
def test_parser_round_trip(instance, keyed):
    L, l, d, _ = instance
    if keyed:
        text = f"!header\nL:{L}\nn:{len(l)}\nl: {' '.join(map(str, l))}\n"
        text += f"d: {' '.join(map(str, d))}\n"
    else:
        text = f"{L}\n" + "".join(f"{a}\t{b}\n" for a, b in zip(l, d, strict=True))
    assert parse_instance(text) == (L, l, d)


@settings(
    max_examples=40,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(instances(max_items=6))
def test_written_file_matches_solution(tmp_path, instance):
    L, l, d, small = instance
    s = tree(L, l, d, small, max_iterations=20)
    path = tmp_path / "out.txt"
    write_solution(s, str(path))
    text = path.read_text()
    assert f"Bars: {s.bars} " in text
    assert f"Leftover: {s.leftover}\n" in text
    assert text.count("Pattern ") == len(s.patterns)


def test_pattern_and_solution_are_immutable():
    s = tree(100, [30, 20], [2, 2])
    with pytest.raises(dataclasses.FrozenInstanceError):
        s.patterns[0].count = 9  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        s.bar_length = 1  # type: ignore[misc]
    assert Pattern(cuts=((30, 2),), waste=40).used == 60


def test_version_matches_pyproject():
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    assert tomllib.loads(pyproject.read_text())["project"]["version"] == __version__
