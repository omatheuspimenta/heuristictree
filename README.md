# heuristictree
[![codecov](https://codecov.io/gh/omatheuspimenta/heuristictree/graph/badge.svg?token=00D8TMX3EX)](https://codecov.io/gh/omatheuspimenta/heuristictree)
[![CI](https://github.com/omatheuspimenta/heuristictree/actions/workflows/pipeline.yaml/badge.svg)](https://github.com/omatheuspimenta/heuristictree/actions/workflows/pipeline.yaml)

Heuristic Methods for Minimizing Cut Bars and Using Leftovers from the One-dimensional Cutting Process - TREE Heuristic.

## Getting Started
#### Dependencies
You need Python 3.11 or later to use **heuristictree**. You can find it at [python.org](https://www.python.org/).

#### Installation
```p
pip install heuristictree
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

## Example
```shell
heuristictree run <your_file.txt>
```



## Output 
The `output.txt` file contains the cutting patterns obtained from executing the `HeuristicTree`.

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
