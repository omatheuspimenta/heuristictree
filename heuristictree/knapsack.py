"""Exact bounded subset-sum ("max fill") used to build cutting patterns."""

from collections.abc import Sequence


def max_fill(
    lengths: Sequence[int],
    bounds: Sequence[int],
    capacity: int,
    min_leftover: int = 0,
) -> list[int]:
    """
    Return the counts of a pattern that fills ``capacity`` as much as possible.

    Solves ``max sum(x_i * l_i)`` subject to ``sum(x_i * l_i) <= capacity`` and
    ``0 <= x_i <= bounds[i]`` exactly, using a bitset dynamic program (bit ``s``
    of a layer is set when length ``s`` is reachable). Among the patterns with
    maximal fill, the one using the fewest copies of the later (smaller) items
    is returned, so larger items are preferred when ``lengths`` is sorted in
    non-increasing order.

    With ``min_leftover > 0`` the fill is *loss-aware*: an unused part in
    ``(0, min_leftover)`` (a loss) is avoided, so the pattern either fills
    ``capacity`` exactly or leaves at least ``min_leftover`` unused. If no
    non-empty pattern satisfies that, the plain maximum fill is returned.

    Example:
    >>> max_fill([50, 40, 30, 20], [2, 4, 6, 8], 100)
    [2, 0, 0, 0]
    >>> max_fill([7, 5], [1, 3], 13)
    [1, 1]
    >>> max_fill([7, 5], [0, 0], 13)
    [0, 0]
    >>> max_fill([7, 5], [1, 3], 13, min_leftover=3)
    [0, 2]
    """
    if len(lengths) != len(bounds):
        raise ValueError("lengths and bounds must have the same size")
    if capacity < 0 or min_leftover < 0:
        raise ValueError("capacity and min_leftover must be non-negative")

    mask = (1 << (capacity + 1)) - 1
    caps = []
    layers = [1]
    reach = 1
    for ln, bound in zip(lengths, bounds, strict=True):
        if ln <= 0 or bound < 0:
            raise ValueError("lengths must be positive and bounds non-negative")
        cap = capacity // ln
        if bound < cap:
            cap = bound
        caps.append(cap)
        # Binary splitting: chunks 1, 2, 4, ... plus the rest cover 0..cap copies.
        remaining, chunk = cap, 1
        while chunk <= remaining:
            reach |= (reach << (chunk * ln)) & mask
            remaining -= chunk
            chunk <<= 1
        if remaining:
            reach |= (reach << (remaining * ln)) & mask
        layers.append(reach)

    target = reach.bit_length() - 1
    if 0 < min_leftover and target != capacity and min_leftover <= capacity:
        allowed = reach & ((1 << (capacity - min_leftover + 1)) - 1)
        if allowed > 1:  # some non-empty pattern leaves a leftover
            target = allowed.bit_length() - 1
    counts = [0] * len(lengths)
    for i in range(len(lengths) - 1, -1, -1):
        previous = layers[i]
        for k in range(caps[i] + 1):
            rest = target - k * lengths[i]
            if rest < 0:
                break
            if (previous >> rest) & 1:
                counts[i] = k
                target = rest
                break
    if target != 0:  # pragma: no cover - guaranteed by the construction above
        raise AssertionError("max_fill backtracking failed")
    return counts
