import importlib.util
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "benchmark", ROOT / "scripts" / "benchmark.py"
)
assert spec and spec.loader
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)


def test_replay_v1_paper_example():
    # v1.0.3 output for the docstring example (it reported bar == 7).
    patterns = [[2, 0, 0, 0], [2, 0, 1], [2, 0, 1], [2, 2], [2, 2], [2, 2]]
    assert benchmark.replay_v1(100, [20, 30, 40, 50], [8, 6, 4, 2], patterns) == (
        6,
        0,
        0,
        True,
    )


def test_replay_v1_recovers_true_waste_of_buggy_patterns():
    # v1.0.3 patterns for the issue reproducer. v1 recorded L_hat = 28 for the
    # second bar although it leaves 500 unused.
    patterns = [
        [0, 1, 0, 0, 0, 1, 2, 1, 0],
        [0, 0, 0, 1, 2, 0, 0],
        [0, 1, 1, 2, 0, 0],
        [1, 1, 1, 0, 1],
        [1, 1],
    ]
    l = [51, 355, 236, 206, 226, 341, 215, 189, 431]
    d = [2, 3, 3, 2, 2, 2, 2, 1, 1]
    bars, leftover, loss, demand_ok = benchmark.replay_v1(1188, l, d, patterns)
    assert (bars, leftover, loss, demand_ok) == (5, 500 + 922, 17 + 20 + 10, True)


def test_replay_v1_rejects_misaligned_pattern():
    with pytest.raises(AssertionError):
        benchmark.replay_v1(100, [20, 30], [1, 1], [[1, 1, 1]])


def test_load_instances():
    instances = benchmark.load_instances(ROOT / "data" / "execution")
    assert len(instances) == 1000
    name, L, l, d = instances[0]
    assert name.endswith(".tar.gz") and L == 1188 and len(l) == len(d) > 0


def test_run_v2_and_summary():
    instance = ("x", 100, [20, 30, 40, 50], [8, 6, 4, 2])
    name, v2 = benchmark.run_v2((instance, "best"))
    assert name == "x" and v2["valid"] and v2["optimal"] and v2["bars"] == 6
    v1 = {
        "bars": 6,
        "leftover": 0,
        "loss": 0,
        "reported_bars": 7,
        "reported_leftover": 0,
        "reported_loss": 0,
        "consistent": False,
        "balanced": True,
        "runtime": 0.0,
    }
    report = benchmark.summarize([instance], {"x": v1}, {"x": v2})
    assert "| Total bars | 6 | 6 |" in report
    assert "equal 1, worse 0" in report
    assert "reported bars != patterns in 1" in report


def has_ref(ref):
    return (
        subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
            cwd=ROOT,
            capture_output=True,
        ).returncode
        == 0
    )


@pytest.mark.skipif(not has_ref("v1.0.3"), reason="tag v1.0.3 not available")
def test_run_v1_from_git(tmp_path):
    benchmark.extract_v1("v1.0.3", tmp_path)
    instance = (
        "x",
        1188,
        [51, 355, 236, 206, 226, 341, 215, 189, 431],
        [2, 3, 3, 2, 2, 2, 2, 1, 1],
    )
    _, v1 = benchmark.run_v1((instance, str(tmp_path)))
    assert (v1["bars"], v1["reported_bars"]) == (5, 6)
    assert (v1["leftover"], v1["loss"]) == (1422, 47)
    assert not v1["balanced"]  # reported leftover + loss disagree with the bars


def test_extract_v1_unknown_ref(tmp_path):
    with pytest.raises(SystemExit):
        benchmark.extract_v1("no-such-ref-xyz", tmp_path)
