from rich.console import Console
from typer import Argument, Context, Exit, Option, Typer

from heuristictree.tree import tree as _tree
from heuristictree.parser import load_file as _load_file
from heuristictree import __version__

app = Typer(rich_markup_mode="rich")
console = Console()


def show_version(flag):
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
):
    message = "Welcome to Heuristic Tree! Type heuristictree --help to see the available commands."
    if ctx.invoked_subcommand:
        return
    console.print(message)


@app.command()
def run(
    path: str = Argument("p", help="path to the file"),
):
    """
    Run the heuristic tree algorithm using a file as input.
    """
    L, l, d = _load_file(path)
    leftover, loss, bar, x_ret = _tree(L, l, d)
    console.print("DONE! Check the output.txt file for the results.", style="green")
