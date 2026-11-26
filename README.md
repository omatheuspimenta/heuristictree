# heuristictree
[![codecov](https://codecov.io/gh/omatheuspimenta/heuristictree/graph/badge.svg?token=00D8TMX3EX)](https://codecov.io/gh/omatheuspimenta/heuristictree)
[![CI](https://github.com/omatheuspimenta/heuristictree/actions/workflows/pipeline.yaml/badge.svg)](https://github.com/omatheuspimenta/heuristictree/actions/workflows/pipeline.yaml)

Heuristic Methods for Minimizing Cut Bars and Using Leftovers from the One-dimensional Cutting Process - TREE Heuristic.

## Getting Started
#### Dependencies
You need Python 3.14 or later to use **heuristictree**. You can find it at [python.org](https://www.python.org/).

#### Installation
```shell
pip install heuristictree      # or: uv tool install heuristictree
```

## Features
In this heuristic, the losses of the cutting process are concentrated on the smallest number of bars possible, using a tree structure, in order to become losses (unusable) into leftovers (usable). 

Example file:
```
1188
229	2
208	1
400	1
327	3
373	3
182	3
285	2
88	1
154	1
83	3
```
First line represents the size of the bar to be cut.  
The other lines represent the size of each item to be cut and the cutting demand, respectively.

## Usage
#### Command line
```shell
heuristictree run <your_file.txt>                 # writes output.txt
heuristictree run <file> -o patterns.txt -m tree  # corrected OptimizationTREE only
heuristictree run <file> --small-item 50          # custom leftover threshold
```
Instance files can use the simple format above or the benchmark format of
`data/execution` (`L:`, `l:` and `d:` lines).

#### Python
```python
from heuristictree.tree import tree

solution = tree(
    1188, [51, 355, 236, 206, 226, 341, 215, 189, 431], [2, 3, 3, 2, 2, 2, 2, 1, 1]
)
solution.bars, solution.leftover, solution.loss  # (4, 281, 0)
for pattern in solution.patterns:
    print(pattern.count, pattern.cuts, pattern.waste)
```
`tree()` never modifies its arguments and only writes a file when
`output_path` is given. Invalid instances (an item longer than the bar,
non-positive lengths, negative demands) raise `ValueError`.

#### Methods
* `best` (default): runs the maximum-fill heuristic and, unless that is already
  provably optimal, the corrected OptimizationTREE; both are improved by a
  seeded local search and the better result is returned.
* `tree`: OptimizationTREE (Algorithm 2 of the paper) with the v1 bugs fixed.
* `maxfill`: each pattern is an exact maximum-fill bounded knapsack.

Solutions are ranked by number of bars, then by loss. A waste smaller than the
smallest demanded item is a loss, otherwise it is a leftover (as in the paper).

## Output
The `output.txt` file contains the number of bars, the leftover and loss, and
every cutting pattern with how many bars use it and its waste.

## Changes in 2.0.0
This is a breaking release.

* Fixed: branch completion overwrote item counts (`x = 1` instead of `x += 1`),
  so the recorded residual `L_hat` disagreed with the pattern and leftover/loss
  were wrong; completions now also respect the item demand.
* Fixed: the bar count was off by one (v1.0.3 reported one bar too many).
* Fixed: an item longer than the bar caused an infinite loop; invalid input now
  raises `ValueError`.
* Fixed: the caller's `l` and `d` lists were modified in place.
* Fixed: the loss threshold now ignores items with zero demand.
* New: `maxfill` and `best` methods, `Solution`/`Pattern` result objects,
  `Solution.validate()`, CLI options, benchmark script.
* Changed: `tree()` returns a `Solution` instead of a tuple and no longer
  appends to `output.txt` (the CLI writes it, overwriting).
* Changed: requires Python 3.14+; the project is built and managed with uv
  (Poetry removed), dependencies updated (typer 0.29, rich 15).

#### Benchmark (`data/execution`, 1,000 instances)
```shell
python scripts/benchmark.py --v1-ref v1.0.3
```
| Metric (1,000 instances) | v1.0.3 | 2.0.0 |
|---|---:|---:|
| Total bars (lower bound 975,917) | 977,391 | 975,918 |
| Total loss | 343,849 | 889 |
| Total leftover | 2,021,404 | 614,440 |
| Total runtime (s), Python 3.14 | 347–407 | 94–104 |
| Invariant violations | 1,000 | 0 |

Per instance, 2.0.0 uses fewer bars in 549 instances, the same bars with less
loss in 430, and is equal in 21 (all of them already optimal); it is never
worse. 991 solutions are provably optimal (bars equal to the lower bound and
the minimum possible loss). v1 values are recomputed from its patterns; it
reported one bar too many everywhere, and wrong leftover/loss in 181 instances.
The total leftover is smaller only because fewer bars leave less unused
material: with the same number of bars, the leftover is never smaller.

## Development
The project uses [uv](https://docs.astral.sh/uv/).
```shell
uv sync                                # create .venv with the dev dependencies
uv run task test                       # format check, lint, tests with coverage
uv run ruff format .                   # apply formatting
uv run python scripts/benchmark.py     # v1.0.3 vs current on data/execution
```
The benchmark reads v1 from the `v1.0.3` git tag (`git fetch origin tag v1.0.3`
if it is missing). In CI it can be started manually from the *Pipeline*
workflow (`benchmark` input) and its table is shown in the run summary.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## Citation
If you use this software in your work, please cite our paper.
> Bressan, G.M.; Pimenta-Zanon, M.H.; Sakuray, F. A Tree-Based Heuristic for the One-Dimensional Cutting Stock Problem Optimization Using Leftovers. Materials 2023, 16, 7133. https://doi.org/10.3390/ma16227133

```bibtex
@article{Bressan2023,
  title = {A Tree-Based Heuristic for the One-Dimensional Cutting Stock Problem Optimization Using Leftovers},
  volume = {16},
  ISSN = {1996-1944},
  url = {http://dx.doi.org/10.3390/ma16227133},
  DOI = {10.3390/ma16227133},
  number = {22},
  journal = {Materials},
  publisher = {MDPI AG},
  author = {Bressan,  Glaucia Maria and Pimenta-Zanon,  Matheus Henrique and Sakuray,  Fabio},
  year = {2023},
  month = nov,
  pages = {7133}
}
```

## License
[MIT](https://choosealicense.com/licenses/mit/)
