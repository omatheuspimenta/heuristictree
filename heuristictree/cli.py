from enum import StrEnum

from rich.console import Console
from rich.table import Table
from typer import Argument, Context, Exit, Option, Typer

from heuristictree import __version__
from heuristictree.parser import load_file
from heuristictree.tree import tree

app = Typer(rich_markup_mode="rich")
console = Console()


class MethodChoice(StrEnum):
    best = "best"
    tree = "tree"
    maxfill = "maxfill"


def show_version(flag: bool) -> None:
    if flag:
        print(f"Heuristic Tree version: {__version__}")
        raise Exit(code=0)


@app.callback(invoke_without_command=True)
def main(
    ctx: Context,
    version: bool = Option(
        False,
        "--version",
        "-v",
        callback=show_version,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    message = (
        "Welcome to Heuristic Tree! "
        "Type heuristictree --help to see the available commands."
    )
    if ctx.invoked_subcommand:
        return
    console.print(message)


@app.command()
def run(
    path: str = Argument(..., help="Path to the instance file."),
    output: str = Option(
        "output.txt", "--output", "-o", help="File the cutting patterns are written to."
    ),
    method: MethodChoice = Option(
        MethodChoice.best, "--method", "-m", help="Heuristic to use."
    ),
    small_item: int = Option(
        0,
        "--small-item",
        "-s",
        help="Leftover threshold (default: smallest demanded item).",
    ),
    seed: int = Option(0, "--seed", help="Seed of the local search."),
) -> None:
    """
    Run the heuristic on an instance file and write the cutting patterns.
    """
    try:
        L, l, d = load_file(path)
        solution = tree(
            L, l, d, small_item, method=method.value, output_path=output, seed=seed
        )
    except (OSError, ValueError) as error:
        console.print(f"Error: {error}", style="red")
        raise Exit(code=1) from None

    table = Table(title=f"heuristictree {__version__} ({solution.method})")
    for column in ("Bars", "Lower bound", "Leftover", "Loss", "Patterns"):
        table.add_column(column, justify="right")
    table.add_row(
        str(solution.bars),
        str(solution.lower_bound),
        str(solution.leftover),
        str(solution.loss),
        str(len(solution.patterns)),
    )
    console.print(table)
    console.print(f"DONE! Cutting patterns written to {output}.", style="green")
