from pytest import fixture, mark
from typer.testing import CliRunner

from heuristictree.cli import app

runner = CliRunner()

FILE_PATH = "data/tests/test.txt"
SAVE_PATH = "data/tests/"


def test_stdout():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0


def test_stdout_without_version():
    result = runner.invoke(app)
    assert result.exit_code == 0


def test_run():
    result = runner.invoke(app, ["run", FILE_PATH])
    assert result.exit_code == 0
