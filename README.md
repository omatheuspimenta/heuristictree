# heuristictree
Example of PyPI package.

## Getting Started
#### Dependencies
You need Python 3.7 or later to use **pacotepypi**. You can find it at [python.org](https://www.python.org/).You also need setuptools, wheel and twine packages, which is available from [PyPI](https://pypi.org). If you have pip, just run:
```
pip install setuptools
pip install wheel
pip install twine
```
#### Installation
Clone this repo to your local machine using:
```
git clone https://github.com/caiocarneloz/pacotepypi.git
```## Features
- File structure for PyPI packages
- Setup with package informations
- License example

## Example
```
import heuristictree as ht

n = 7
L = 30
l = [7, 9, 11, 14, 19, 21, 26]
d = [2, 3, 2, 2, 2, 1, 1]

left = loss = bar = 0
x = []

left,loss,bar,x = ht.tree(L=L, n=n, l=l, d=d)
```
