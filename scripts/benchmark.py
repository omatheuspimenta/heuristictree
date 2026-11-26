"""
Benchmark heuristictree v2 against a v1 release on ``data/execution``.

Usage:
    python scripts/benchmark.py [--v1-ref v1.0.3] [--method best] [--jobs 4]
                                [--json results.json] [--data data/execution]

The v1 code is read from git (``git show <ref>:heuristictree/tree.py``), so the
comparison is reproducible from the repository alone. v1's reported leftover
and loss are not reliable (its residual bookkeeping is wrong), so its *true*
values are recomputed by replaying the patterns it returns; both are shown.
Every v2 solution is checked with ``Solution.validate()``.
"""

from __future__ import annotations

import argparse
import glob
import importlib.util
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import time
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from heuristictree.parser import parse_instance  # noqa: E402
from heuristictree.tree import tree  # noqa: E402

Instance = tuple[str, int, list[int], list[int]]


def load_instances(data_dir: Path) -> list[Instance]:
    instances = []
    for archive in sorted(glob.glob(str(data_dir / "*" / "*.tar.gz"))):
        with tarfile.open(archive) as tar:
            for member in tar.getmembers():
                if not member.isfile():
                    continue
                handle = tar.extractfile(member)
                assert handle is not None
                text = handle.read().decode("utf-8")
                name = os.path.relpath(archive, data_dir)
                instances.append((name, *parse_instance(text, name)))
    return instances


def extract_v1(ref: str, target: Path) -> Path:
    for module in ("tree", "quick_tree"):
        result = subprocess.run(
            ["git", "show", f"{ref}:heuristictree/{module}.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            sys.exit(
                f"cannot read {module}.py at git ref {ref!r} "
                f"(try `git fetch origin tag {ref}`): {result.stderr.strip()}"
            )
        source = result.stdout
        source = source.replace(
            "from heuristictree.quick_tree import", "from quick_tree import"
        )
        (target / f"{module}.py").write_text(source)
    return target


def replay_v1(L: int, l: list[int], d: list[int], patterns: list[list[int]]):
    """True (bars, leftover, loss, cut pieces) of v1 patterns."""
    merged: Counter[int] = Counter()
    for length, qty in zip(l, d, strict=True):
        merged[length] += qty
    lengths = sorted(merged, reverse=True)
    remaining = [merged[x] for x in lengths]
    small = lengths[-1]
    leftover = loss = 0
    cut: Counter[int] = Counter()
    active = list(range(len(lengths)))
    for x in patterns:
        assert len(x) == len(active), "v1 pattern does not match its item list"
        used = 0
        for i, k in zip(active, x, strict=True):
            used += lengths[i] * k
            remaining[i] -= k
            cut[lengths[i]] += k
        assert used <= L, "v1 pattern exceeds bar length"
        waste = L - used
        if waste < small:
            loss += waste
        else:
            leftover += waste
        active = [i for i in active if remaining[i] != 0]
    wanted = {k: v for k, v in merged.items() if v > 0}
    return len(patterns), leftover, loss, dict(+cut) == wanted


def run_v1(job: tuple[Instance, str]) -> tuple[str, dict]:
    (name, L, l, d), v1_dir = job
    sys.path.insert(0, v1_dir)
    spec = importlib.util.spec_from_file_location("v1_tree", Path(v1_dir) / "tree.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory() as tmp:  # v1 appends to ./output.txt
        cwd = os.getcwd()
        os.chdir(tmp)
        try:
            start = time.perf_counter()
            leftover, loss, bar, patterns = module.tree(L, list(l), list(d))
            runtime = time.perf_counter() - start
        finally:
            os.chdir(cwd)
    bars, true_leftover, true_loss, demand_ok = replay_v1(L, l, d, patterns)
    items = sum(a * b for a, b in zip(l, d, strict=True))
    balanced = leftover + loss + items == bars * L
    consistent = bar == bars and balanced and demand_ok
    return name, {
        "bars": bars,
        "leftover": true_leftover,
        "loss": true_loss,
        "reported_bars": bar,
        "reported_leftover": leftover,
        "reported_loss": loss,
        "consistent": consistent,
        "balanced": balanced,
        "runtime": runtime,
    }


def run_v2(job: tuple[Instance, str]) -> tuple[str, dict]:
    (name, L, l, d), method = job
    start = time.perf_counter()
    solution = tree(L, l, d, method=method)
    runtime = time.perf_counter() - start
    try:
        solution.validate()
        valid = True
    except AssertionError:
        valid = False
    waste = solution.bars * L - sum(a * b for a, b in zip(l, d, strict=True))
    loss_floor = waste if waste < solution.small_item else 0
    return name, {
        "bars": solution.bars,
        "leftover": solution.leftover,
        "loss": solution.loss,
        "lower_bound": solution.lower_bound,
        "optimal": solution.bars == solution.lower_bound
        and solution.loss == loss_floor,
        "valid": valid,
        "runtime": runtime,
    }


def summarize(instances: list[Instance], v1: dict, v2: dict) -> str:
    n = len(instances)
    total = lambda res, key: sum(r[key] for r in res.values())  # noqa: E731
    better_bars = better_loss = equal = worse = changed = 0
    for name, *_ in instances:
        old = (v1[name]["bars"], v1[name]["loss"])
        new = (v2[name]["bars"], v2[name]["loss"])
        changed += old != new or v1[name]["leftover"] != v2[name]["leftover"]
        if new < old:
            if new[0] < old[0]:
                better_bars += 1
            else:
                better_loss += 1
        elif new == old:
            equal += 1
        else:
            worse += 1
    optimal = sum(r["optimal"] for r in v2.values())
    rows = [
        ("Total bars", total(v1, "bars"), total(v2, "bars")),
        ("Mean bars", total(v1, "bars") / n, total(v2, "bars") / n),
        ("Total leftover", total(v1, "leftover"), total(v2, "leftover")),
        ("Mean leftover", total(v1, "leftover") / n, total(v2, "leftover") / n),
        ("Total loss", total(v1, "loss"), total(v2, "loss")),
        ("Mean loss", total(v1, "loss") / n, total(v2, "loss") / n),
        ("Total runtime (s)", total(v1, "runtime"), total(v2, "runtime")),
        ("Mean runtime (s)", total(v1, "runtime") / n, total(v2, "runtime") / n),
        (
            "Invariant violations",
            sum(not r["consistent"] for r in v1.values()),
            sum(not r["valid"] for r in v2.values()),
        ),
    ]
    fmt = lambda v: f"{v:,.4f}" if isinstance(v, float) else f"{v:,}"  # noqa: E731
    lines = [
        f"Instances: {n}   lower bound (sum of B_bar): "
        f"{sum(r['lower_bound'] for r in v2.values()):,}",
        "",
        "| Metric | v1 | v2 |",
        "|---|---:|---:|",
        *(f"| {m} | {fmt(a)} | {fmt(b)} |" for m, a, b in rows),
        "",
        f"v1 reported totals: bars {total(v1, 'reported_bars'):,}, "
        f"leftover {total(v1, 'reported_leftover'):,}, "
        f"loss {total(v1, 'reported_loss'):,}",
        f"Instances whose result (bars, leftover, loss) changed: {changed}",
        f"v2 vs v1 per instance (bars, then loss): fewer bars {better_bars}, "
        f"same bars and less loss {better_loss}, equal {equal}, worse {worse}",
        "v1 inconsistencies: reported bars != patterns in "
        f"{sum(r['reported_bars'] != r['bars'] for r in v1.values())}, "
        "reported leftover + loss != unused length in "
        f"{sum(not r['balanced'] for r in v1.values())}",
        "v2 provably optimal (bars == B_bar and loss is the unavoidable minimum): "
        f"{optimal}",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--v1-ref", default="v1.0.3")
    parser.add_argument("--method", default="best", choices=("best", "tree", "maxfill"))
    parser.add_argument("--jobs", type=int, default=os.cpu_count() or 1)
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "execution")
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()

    instances = load_instances(args.data)
    with tempfile.TemporaryDirectory() as v1_dir, Pool(args.jobs) as pool:
        extract_v1(args.v1_ref, Path(v1_dir))
        v1 = dict(pool.map(run_v1, [(i, v1_dir) for i in instances], chunksize=1))
        v2 = dict(pool.map(run_v2, [(i, args.method) for i in instances], chunksize=1))
    report = summarize(instances, v1, v2)
    print(report)
    if args.json:
        args.json.write_text(json.dumps({"v1": v1, "v2": v2}, indent=1))


if __name__ == "__main__":
    main()
