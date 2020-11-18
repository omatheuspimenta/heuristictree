# heuristictree
Heuristic Methods for Minimizing Cut Bars and Using Leftovers from the One-dimensional Cutting Process - TREE Heuristic.

## Getting Started
#### Dependencies
You need Python 3.8 or later to use **heuristictree**. You can find it at [python.org](https://www.python.org/).

#### Installation
Clone this repo to your local machine using:
```
git clone https://github.com/omatheuspimenta/heuristictree
```
## Features
- Soon

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
