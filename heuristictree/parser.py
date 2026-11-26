"""Instance file readers."""

from pathlib import Path


def load_file(path: str | Path) -> tuple[int, list[int], list[int]]:
    """
    Read an instance file and return ``(L, l, d)``.

    Two formats are accepted:

    * Simple: the first line is the bar length, every other line holds an item
      length and its demand (``"229 2"``).
    * Benchmark (``data/execution``): lines ``L: <bar length>``,
      ``l: <lengths...>`` and ``d: <demands...>``; other keys (such as ``n:``)
      and comment lines starting with ``!`` are ignored.

    Blank lines are ignored. Malformed files raise ``ValueError``.
    """
    return parse_instance(Path(path).read_text(encoding="utf-8"), str(path))


def parse_instance(
    text: str, source: str = "<string>"
) -> tuple[int, list[int], list[int]]:
    r"""
    Parse instance ``text`` (see :func:`load_file` for the formats).

    >>> parse_instance("100\n20 3\n30 1\n")
    (100, [20, 30], [3, 1])
    >>> parse_instance("!comment\nL:100\nn:2\nl: 20 30\nd: 3 1\n")
    (100, [20, 30], [3, 1])
    """
    lines = [
        (number, line.strip())
        for number, line in enumerate(text.splitlines(), start=1)
        if line.strip() and not line.lstrip().startswith("!")
    ]
    if not lines:
        raise ValueError(f"{source}: empty instance file")
    if ":" in lines[0][1]:
        return _parse_keyed(source, lines)
    return _parse_simple(source, lines)


def _ints(source: str, number: int, fields: list[str]) -> list[int]:
    try:
        return [int(value) for value in fields]
    except ValueError:
        raise ValueError(
            f"{source}:{number}: expected integers, got {fields}"
        ) from None


def _parse_simple(
    source: str, lines: list[tuple[int, str]]
) -> tuple[int, list[int], list[int]]:
    number, first = lines[0]
    header = _ints(source, number, first.split())
    if len(header) != 1:
        raise ValueError(f"{source}:{number}: first line must be the bar length")
    l: list[int] = []
    d: list[int] = []
    for number, line in lines[1:]:
        fields = _ints(source, number, line.split())
        if len(fields) != 2:
            raise ValueError(f"{source}:{number}: expected '<length> <demand>'")
        l.append(fields[0])
        d.append(fields[1])
    return header[0], l, d


def _parse_keyed(
    source: str, lines: list[tuple[int, str]]
) -> tuple[int, list[int], list[int]]:
    values: dict[str, list[int]] = {}
    for number, line in lines:
        key, sep, rest = line.partition(":")
        if not sep:
            raise ValueError(f"{source}:{number}: expected '<key>: <values>'")
        values[key.strip()] = _ints(source, number, rest.split())
    missing = [key for key in ("L", "l", "d") if key not in values]
    if missing:
        raise ValueError(f"{source}: missing keys {missing}")
    if len(values["L"]) != 1:
        raise ValueError(f"{source}: 'L:' must hold a single value")
    if len(values["l"]) != len(values["d"]):
        raise ValueError(f"{source}: 'l:' and 'd:' have different sizes")
    return values["L"][0], values["l"], values["d"]
