from typer.testing import CliRunner

from heuristictree import __version__
from heuristictree.cli import app

runner = CliRunner()

FILE_PATH = "data/tests/test.txt"


def test_stdout():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_stdout_without_version():
    result = runner.invoke(app)
    assert result.exit_code == 0


def test_run(tmp_path):
    out = tmp_path / "output.txt"
    result = runner.invoke(app, ["run", FILE_PATH, "--output", str(out)])
    assert result.exit_code == 0, result.stdout
    assert "DONE!" in result.stdout
    assert out.read_text().startswith("Method: best")


def test_run_default_output(tmp_path, monkeypatch):
    path = tmp_path / "inst.txt"
    path.write_text("100\n20 8\n30 6\n40 4\n50 2\n")
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["run", str(path), "-m", "tree", "-s", "10"])
    assert result.exit_code == 0, result.stdout
    assert (tmp_path / "output.txt").exists()


def test_run_missing_file(tmp_path):
    result = runner.invoke(app, ["run", str(tmp_path / "missing.txt")])
    assert result.exit_code == 1
    assert "Error" in result.stdout


def test_run_invalid_instance(tmp_path):
    path = tmp_path / "bad.txt"
    path.write_text("100\n120 1\n")
    result = runner.invoke(app, ["run", str(path), "-o", str(tmp_path / "o.txt")])
    assert result.exit_code == 1
    assert "does not fit" in result.stdout
