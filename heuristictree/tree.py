"""
OptimizationTREE and improved heuristics for the one-dimensional cutting stock
problem with usable leftovers.

Reference:
    Bressan, G.M.; Pimenta-Zanon, M.H.; Sakuray, F. A Tree-Based Heuristic for
    the One-Dimensional Cutting Stock Problem Optimization Using Leftovers.
    Materials 2023, 16, 7133. https://doi.org/10.3390/ma16227133

The unused part of a bar (its *waste*) is classified as in the paper: it is a
**loss** when it is smaller than the smallest demanded item and a **leftover**
otherwise. All objective values are derived from the returned patterns, so the
reported bars, leftover and loss always describe the patterns exactly.
"""

from __future__ import annotations

import random
from bisect import bisect_right
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Literal

from heuristictree.knapsack import max_fill

Method = Literal["best", "tree", "maxfill"]
METHODS: tuple[str, ...] = ("best", "tree", "maxfill")

# A bar is stored internally as a sorted tuple of (item index, count) pairs.
_Bar = tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class Pattern:
    """A cutting pattern applied to ``count`` identical bars."""

    cuts: tuple[tuple[int, int], ...]
    """``(item length, number of pieces)`` pairs, longest item first."""
    waste: int
    """Unused length of each bar cut with this pattern."""
    count: int = 1
    """Number of bars cut with this pattern."""

    @property
    def used(self) -> int:
        """Length of each bar that is turned into items."""
        return sum(length * pieces for length, pieces in self.cuts)


@dataclass(frozen=True)
class Solution:
    """Result of a cutting stock heuristic."""

    bar_length: int
    small_item: int
    """Threshold separating loss (``waste < small_item``) from leftover."""
    patterns: tuple[Pattern, ...]
    method: str
    lower_bound: int
    """``ceil(sum(l_i * d_i) / L)``, Equation (3) of the paper."""
    demand: dict[int, int] = field(repr=False)
    """Demanded pieces per item length (after merging equal lengths)."""

    @property
    def bars(self) -> int:
        """Total number of bars cut."""
        return sum(p.count for p in self.patterns)

    @property
    def loss(self) -> int:
        """Sum of the wastes smaller than ``small_item``."""
        return sum(
            p.waste * p.count for p in self.patterns if p.waste < self.small_item
        )

    @property
    def leftover(self) -> int:
        """Sum of the wastes greater than or equal to ``small_item``."""
        return sum(
            p.waste * p.count for p in self.patterns if p.waste >= self.small_item
        )

    def cut_items(self) -> dict[int, int]:
        """Number of pieces cut per item length."""
        total: Counter[int] = Counter()
        for p in self.patterns:
            for length, pieces in p.cuts:
                total[length] += pieces * p.count
        return dict(total)

    def validate(self) -> None:
        """
        Raise ``AssertionError`` if any invariant of the solution is broken.

        Checked: every pattern fits in the bar and records its true waste,
        counts are positive, the demand is met exactly, and
        ``leftover + loss + sum(l_i * d_i) == bars * L``.
        """
        L = self.bar_length
        for p in self.patterns:
            assert p.count > 0, f"non-positive pattern count: {p}"
            assert p.cuts, f"empty pattern: {p}"
            assert all(pieces > 0 for _, pieces in p.cuts), f"bad pieces: {p}"
            assert p.used <= L, f"pattern exceeds bar length: {p}"
            assert p.waste == L - p.used, f"wrong recorded waste: {p}"
        wanted = {k: v for k, v in self.demand.items() if v > 0}
        assert self.cut_items() == wanted, "cut items differ from the demand"
        items = sum(length * qty for length, qty in wanted.items())
        assert self.leftover + self.loss + items == self.bars * L, "length balance"
        assert self.bars >= self.lower_bound, "fewer bars than the lower bound"


@dataclass(frozen=True)
class _Instance:
    L: int
    lengths: tuple[int, ...]  # distinct, strictly decreasing
    demand: tuple[int, ...]  # positive
    small: int

    @property
    def lower_bound(self) -> int:
        total = sum(a * b for a, b in zip(self.lengths, self.demand, strict=True))
        return -(-total // self.L)

    def waste(self, bar: _Bar) -> int:
        return self.L - sum(self.lengths[i] * k for i, k in bar)


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def tree(
    L: int,
    l: Sequence[int],
    d: Sequence[int],
    smallitem: int = 0,
    *,
    method: Method = "best",
    output_path: str | None = None,
    seed: int = 0,
    max_iterations: int = 3000,
) -> Solution:
    """
    Solve a one-dimensional cutting stock problem with usable leftovers.

    Parameters:
        L: Bar length.
        l: Item lengths (equal lengths are merged).
        d: Item demands, aligned with ``l``.
        smallitem: Leftover threshold. Wastes smaller than it are losses. When
            0, the smallest length with positive demand is used (paper, Alg. 2).
        method: ``"tree"`` is the corrected OptimizationTREE of the paper,
            ``"maxfill"`` builds each pattern by an exact maximum-fill
            knapsack, and ``"best"`` (default) runs both and improves the
            better one with a seeded local search.
        output_path: If given, the solution is written to this text file.
        seed: Seed of the local search (results are deterministic).
        max_iterations: Iteration limit of the local search.

    Returns:
        A :class:`Solution`. ``l`` and ``d`` are not modified.

    Example:
    >>> s = tree(100, [20, 30, 40, 50], [8, 6, 4, 2])
    >>> s.bars, s.leftover, s.loss
    (6, 0, 0)
    >>> s = tree(1188, [51, 355, 236, 206, 226, 341, 215, 189, 431],
    ...          [2, 3, 3, 2, 2, 2, 2, 1, 1], method="tree")
    >>> s.bars, s.leftover, s.loss
    (4, 201, 80)
    """
    if method not in METHODS:
        raise ValueError(f"method must be one of {METHODS}, got {method!r}")
    if max_iterations < 0:
        raise ValueError("max_iterations must be non-negative")
    inst = _prepare(L, l, d, smallitem)

    if method == "tree":
        bars = _optimization_tree(inst)
    elif method == "maxfill":
        bars = _sequential_max_fill(inst, range(len(inst.lengths)), inst.demand)
    else:
        rng = random.Random(seed)
        start = _sequential_max_fill(inst, range(len(inst.lengths)), inst.demand)
        bars = _local_search(inst, start, rng, max_iterations)
        if not _is_optimal(inst, bars):
            # Portfolio: also start from the corrected OptimizationTREE.
            other = _local_search(inst, _optimization_tree(inst), rng, max_iterations)
            bars = min(bars, other, key=lambda c: _score(inst, c))

    solution = _build_solution(inst, bars, method)
    solution.validate()
    if output_path is not None:
        write_solution(solution, output_path)
    return solution


def write_solution(solution: Solution, path: str) -> None:
    """Write ``solution`` to ``path`` as human-readable text (overwrites)."""
    lines = [
        f"Method: {solution.method}",
        f"Bar length: {solution.bar_length}",
        f"Bars: {solution.bars} (lower bound {solution.lower_bound})",
        f"Leftover: {solution.leftover}",
        f"Loss: {solution.loss} (waste < {solution.small_item})",
        "",
    ]
    for number, p in enumerate(solution.patterns, start=1):
        kind = (
            "none"
            if p.waste == 0
            else ("loss" if p.waste < solution.small_item else "leftover")
        )
        lines.append(f"Pattern {number}: {p.count} bar(s), waste {p.waste} ({kind})")
        lines.extend(f"  {pieces} x {length}" for length, pieces in p.cuts)
        lines.append("")
    with open(path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))


# --------------------------------------------------------------------------- #
# Preprocessing and solution assembly
# --------------------------------------------------------------------------- #
def _prepare(L: int, l: Sequence[int], d: Sequence[int], smallitem: int) -> _Instance:
    if not _is_int(L) or L <= 0:
        raise ValueError(f"bar length must be a positive integer, got {L!r}")
    if len(l) != len(d):
        raise ValueError("l and d must have the same size")
    if not _is_int(smallitem) or smallitem < 0:
        raise ValueError("smallitem must be a non-negative integer")
    merged: Counter[int] = Counter()
    for length, demand in zip(l, d, strict=True):
        if not _is_int(length) or not _is_int(demand):
            raise ValueError("lengths and demands must be integers")
        if length <= 0:
            raise ValueError(f"item lengths must be positive, got {length}")
        if demand < 0:
            raise ValueError(f"demands must be non-negative, got {demand}")
        if demand > 0 and length > L:
            raise ValueError(f"item of length {length} does not fit in bar {L}")
        if demand > 0:
            merged[length] += demand
    lengths = tuple(sorted(merged, reverse=True))
    demand = tuple(merged[length] for length in lengths)
    small = smallitem or (lengths[-1] if lengths else 0)
    return _Instance(L, lengths, demand, small)


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _build_solution(inst: _Instance, bars: Counter[_Bar], method: str) -> Solution:
    def order(item: tuple[_Bar, int]) -> tuple[int, tuple[int, ...]]:
        bar, _ = item
        return (inst.waste(bar), tuple(-inst.lengths[i] for i, _ in bar))

    patterns = tuple(
        Pattern(
            cuts=tuple((inst.lengths[i], k) for i, k in bar),
            waste=inst.waste(bar),
            count=count,
        )
        for bar, count in sorted(bars.items(), key=order)
        if count > 0
    )
    return Solution(
        bar_length=inst.L,
        small_item=inst.small,
        patterns=patterns,
        method=method,
        lower_bound=inst.lower_bound,
        demand=dict(zip(inst.lengths, inst.demand, strict=True)),
    )


def _to_bar(indices: Sequence[int], counts: Sequence[int]) -> _Bar:
    return tuple(sorted((i, k) for i, k in zip(indices, counts, strict=True) if k > 0))


def _score(inst: _Instance, bars: Counter[_Bar]) -> tuple[int, int]:
    """Lexicographic objective: (number of bars, loss)."""
    n_bars = loss = 0
    for bar, count in bars.items():
        n_bars += count
        waste = inst.waste(bar)
        if waste < inst.small:
            loss += waste * count
    return n_bars, loss


def _is_optimal(inst: _Instance, bars: Counter[_Bar]) -> bool:
    """
    True when (bars, loss) provably cannot be improved.

    That is the case when the number of bars equals the lower bound and the
    loss is zero, or the whole (unavoidable) waste is below the threshold.
    """
    n_bars, loss = _score(inst, bars)
    if n_bars != inst.lower_bound:
        return False
    waste = n_bars * inst.L - sum(
        a * b for a, b in zip(inst.lengths, inst.demand, strict=True)
    )
    return loss == (waste if waste < inst.small else 0)


# --------------------------------------------------------------------------- #
# Corrected OptimizationTREE (paper, Algorithms 1 and 2)
# --------------------------------------------------------------------------- #
def _optimization_tree(inst: _Instance) -> Counter[_Bar]:
    """
    OptimizationTREE with the v1 bugs fixed.

    Each bar is built by :func:`_tree_pattern` on the items whose demand is
    still positive. When every remaining demand is at least ``L // l_i`` the
    demand cannot influence the pattern, so the same pattern is repeated for
    as long as that holds instead of being recomputed.
    """
    L = inst.L
    remaining = list(inst.demand)
    bars: Counter[_Bar] = Counter()
    while True:
        active = [i for i, q in enumerate(remaining) if q > 0]
        if not active:
            return bars
        lengths = [inst.lengths[i] for i in active]
        demand = [remaining[i] for i in active]
        counts = _tree_pattern(L, lengths, demand)
        repeat = 1
        caps = [L // length for length in lengths]
        if all(q >= c for q, c in zip(demand, caps, strict=True)):
            repeat += min(
                (q - c) // k
                for q, c, k in zip(demand, caps, counts, strict=True)
                if k > 0
            )
        for i, k in zip(active, counts, strict=True):
            remaining[i] -= k * repeat
        bars[_to_bar(active, counts)] += repeat


def _tree_pattern(L: int, l: Sequence[int], d: Sequence[int]) -> list[int]:
    """
    Build one cutting pattern with the OptimizationTREE branching rule.

    ``l`` is strictly decreasing and every ``d`` is positive. The first branch
    is the first-fit selection of Algorithm 1. Branch ``c`` keeps one piece
    fewer of item ``c - 1``, fills the bar greedily with items ``c..n-1`` and
    tries to complete the residual with one piece of a larger item. The branch
    with the smallest residual is returned.

    Bug fixes relative to v1.0.x: completing pieces are *added* (``+= 1``)
    instead of overwriting the count, and are only added while the demand of
    that item allows it, so the pattern and its residual always agree and
    ``0 <= x_i <= d_i`` holds.

    >>> _tree_pattern(1188, [431, 355, 341, 236, 226, 215, 51], [1, 2, 2, 3, 2, 1, 2])
    [0, 0, 0, 3, 2, 0, 0]
    """
    n = len(l)
    smallest = l[-1]

    # First branch: selection of ordered items (Algorithm 1).
    best = [0] * n
    best_residual = L
    for i in range(n):
        best[i] = min(best_residual // l[i], d[i])
        best_residual -= best[i] * l[i]
        if best_residual < smallest:
            break

    branch = [0] * n
    branch[0] = best[0]
    residual = L
    level = 1
    while residual != 0 and level != n:
        kept = max(branch[level - 1] - 1, 0)
        branch = [0] * n
        branch[level - 1] = kept
        residual = L - l[level - 1] * kept
        larger = l[:level]
        for j in range(level, n):
            branch[j] = min(residual // l[j], d[j])
            residual -= branch[j] * l[j]
            if residual <= l[level]:
                continue
            exact = larger.index(residual) if residual in larger else -1
            if exact >= 0 and branch[exact] < d[exact]:
                branch[exact] += 1
                residual = 0
                continue
            for k in range(level):
                gap = residual - l[k]
                if 0 <= gap < best_residual and branch[k] < d[k]:
                    branch[k] += 1
                    residual = gap
                    break
        if residual < best_residual:
            best_residual = residual
            best = branch
        level += 1

    assert (
        sum(x * length for x, length in zip(best, l, strict=True)) == L - best_residual
    )
    return best


# --------------------------------------------------------------------------- #
# Sequential maximum-fill heuristic
# --------------------------------------------------------------------------- #
def _sequential_max_fill(
    inst: _Instance,
    indices: Iterable[int],
    demand: Sequence[int],
    loss_aware: bool = False,
) -> Counter[_Bar]:
    """
    Cut the items ``indices`` (with ``demand`` aligned to them) bar by bar.

    Every pattern is an exact maximum-fill knapsack over the remaining items,
    so the waste is pushed to the last bars, where it is large enough to be a
    leftover. With ``loss_aware`` a bar is either filled exactly or left with
    at least ``small`` unused (see :func:`max_fill`), which turns would-be
    losses into leftovers. Each pattern is repeated as many times as the
    demand allows.
    """
    idx = list(indices)
    remaining = list(demand)
    lengths = [inst.lengths[i] for i in idx]
    bars: Counter[_Bar] = Counter()
    while any(remaining):
        rest = sum(q * ln for q, ln in zip(remaining, lengths, strict=True))
        # Everything left fits in one bar: splitting it would only add bars.
        min_leftover = inst.small if loss_aware and rest > inst.L else 0
        counts = max_fill(lengths, remaining, inst.L, min_leftover)
        repeat = min(q // k for q, k in zip(remaining, counts, strict=True) if k > 0)
        for j, k in enumerate(counts):
            remaining[j] -= k * repeat
        bars[_to_bar(idx, counts)] += repeat
    return bars


def _best_fit(
    inst: _Instance,
    order: Sequence[int],
    items: Counter[int],
    rng: random.Random | None = None,
) -> Counter[_Bar]:
    """
    Best-fit packing of ``items`` (pieces per item index).

    Pieces are taken in ``order`` (item by item) or, with ``rng``, in a random
    order; each goes to the open bar with the least free space that still
    fits it, or opens a new bar. It can pack into fewer bars than sequential
    maximum fill when the best packing needs several partially filled bars.
    """
    pieces = [i for i in order for _ in range(items[i])]
    if rng is not None:
        rng.shuffle(pieces)
    free: list[int] = []
    loads: list[Counter[int]] = []
    for i in pieces:
        length = inst.lengths[i]
        fits = [b for b, f in enumerate(free) if f >= length]
        if fits:
            b = min(fits, key=free.__getitem__)
        else:
            b = len(free)
            free.append(inst.L)
            loads.append(Counter())
        free[b] -= length
        loads[b][i] += 1
    return Counter(tuple(sorted(load.items())) for load in loads)


# --------------------------------------------------------------------------- #
# Local search
# --------------------------------------------------------------------------- #
def _local_search(
    inst: _Instance,
    bars: Counter[_Bar],
    rng: random.Random,
    max_iterations: int,
    pool_size: int = 40,
    patience: int = 1000,
) -> Counter[_Bar]:
    """
    Improve ``bars`` lexicographically on (number of bars, loss).

    Each iteration removes a pool of bars (every bar with waste, sampled if
    there are too many, plus some random full bars), cuts their items again
    with :func:`_sequential_max_fill` and keeps the new bars when the
    pool's score does not get worse. The repacking cycles through six modes:
    maximum fill, loss-aware fill and best-fit, each with items in decreasing
    or random order (random orders break ties differently). Stops early at a
    provable optimum or after ``patience`` iterations without improvement.
    """
    bars = Counter(bars)
    stale = 0
    for iteration in range(max_iterations):
        if _is_optimal(inst, bars) or stale >= patience:
            break

        open_bars: list[_Bar] = []
        full_keys: list[_Bar] = []
        full_ends: list[int] = []  # cumulative counts of full_keys
        for bar, count in bars.items():
            if inst.waste(bar) > 0:
                open_bars.extend([bar] * count)
            else:
                full_keys.append(bar)
                full_ends.append((full_ends[-1] if full_ends else 0) + count)
        if len(open_bars) > pool_size // 2:
            open_bars = rng.sample(open_bars, pool_size // 2)
        n_full = full_ends[-1] if full_ends else 0
        extra = min(n_full, max(pool_size - len(open_bars), 2))
        pool = open_bars + [
            full_keys[bisect_right(full_ends, position)]
            for position in rng.sample(range(n_full), extra)
        ]
        if len(pool) < 2:
            break

        items: Counter[int] = Counter()
        for bar in pool:
            for i, k in bar:
                items[i] += k
        order = sorted(items, key=lambda i: -inst.lengths[i])
        mode = iteration % 6
        if mode % 2:
            rng.shuffle(order)
        if mode < 4:
            new = _sequential_max_fill(
                inst, order, [items[i] for i in order], loss_aware=mode >= 2
            )
        else:
            new = _best_fit(inst, order, items, rng if mode == 5 else None)

        old = Counter(pool)
        if _score(inst, new) <= _score(inst, old):
            improved = _score(inst, new) < _score(inst, old)
            bars.subtract(old)
            bars.update(new)
            bars = +bars
            stale = 0 if improved else stale + 1
        else:
            stale += 1
    return bars
