# ndplex

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24054477.svg)](https://doi.org/10.5281/zenodo.24054477)

**The n-Dimensional m-Plex array: a generic Pascal's array for NumPy.**

`ndplex` builds Pascal's rectangle, cube or hypercube as a NumPy array, and lets you change everything that defines it: the values on its edges, the rule that generates each interior node, and which neighbours that rule reads. It can then cut lines and cross-sections through the array, show the array as a triangle, tetrahedron or n-simplex, and look its rows up in the [On-Line Encyclopedia of Integer Sequences](https://oeis.org).

## Install

```
pip install ndplex
```

In Google Colab, run `!pip install ndplex` in a cell. ndplex needs Python 3.10 or later and NumPy 1.23.5 or later, nothing else. `oeis` needs a network connection when it is called.

## Quick start

By default, `ndplex(n)` is Pascal's rectangle: ones on the top and left edges, and every other node the sum of the node above it and the node to its left.

```pycon
>>> from ndplex import ndplex
>>> p = ndplex(6)
>>> print(p)
[[  1   1   1   1   1   1]
 [  1   2   3   4   5   6]
 [  1   3   6  10  15  21]
 [  1   4  10  20  35  56]
 [  1   5  15  35  70 126]
 [  1   6  21  56 126 252]]
```

`as_tri` shows the same array as Pascal's triangle, justified left, or returns the sum of each row.

```pycon
>>> print(p.as_tri())
[[ 1  0  0  0  0  0]
 [ 1  1  0  0  0  0]
 [ 1  2  1  0  0  0]
 [ 1  3  3  1  0  0]
 [ 1  4  6  4  1  0]
 [ 1  5 10 10  5  1]]
>>> print(p.as_tri(sums=True))
[ 1  2  4  8 16 32]
```

`diag` walks through the array from a starting node by a fixed step. Row 4 of the triangle is an anti-diagonal of the rectangle; the main diagonal holds the central binomial coefficients.

```pycon
>>> print(p.diag(loc=(4, 0), move=(-1, 1)))
[1 4 6 4 1]
>>> print(p.diag())
[  1   2   6  20  70 252]
```

The steeper diagonals sum to the Fibonacci numbers:

```pycon
>>> f = ndplex(10)
>>> print([int(f.diag(loc=(k, 0), move=(-2, 1)).sum()) for k in range(10)])
[1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
```

## Other arrays

`ndplex(nrows, edges=(1, 1), arg_locs=None, func=sum, dtype=np.int64)`

- **`edges`** sets the front edges, as numbers or as sequences of length `nrows`. Their number sets the dimension. In 2-D, `edges[0]` fills column 0 and `edges[1]` fills row 0.
- **`func`** generates each interior node from a list of argument values. The default is `sum`.
- **`arg_locs`** gives where those arguments are, relative to the node. The default in 2-D is `[[-1, 0], [0, -1]]`, the nodes above and to the left. A `None` coordinate means "on the edge".

Odd numbers along the top edge give the squares, the square pyramidal numbers, and so on down the rows:

```pycon
>>> print(ndplex(5, edges=(1, [1, 3, 5, 7, 9])))
[[  1   3   5   7   9]
 [  1   4   9  16  25]
 [  1   5  14  30  55]
 [  1   6  20  50 105]
 [  1   7  27  77 182]]
```

Pascal's rule modulo 2 gives the Sierpinski pattern:

```pycon
>>> print(ndplex(6, func=lambda x: sum(x) % 2))
[[1 1 1 1 1 1]
 [1 0 1 0 1 0]
 [1 1 0 0 1 1]
 [1 0 0 0 1 0]
 [1 1 1 1 0 0]
 [1 0 1 0 0 0]]
```

Adding the diagonal neighbour as a third argument gives the Delannoy numbers:

```pycon
>>> print(ndplex(6, arg_locs=[[-1, 0], [0, -1], [-1, -1]]))
[[   1    1    1    1    1    1]
 [   1    3    5    7    9   11]
 [   1    5   13   25   41   61]
 [   1    7   25   63  129  231]
 [   1    9   41  129  321  681]
 [   1   11   61  231  681 1683]]
```

## Higher dimensions

Three edges make Pascal's cube; `as_tri` shows it as a tetrahedron, layer by layer. Each layer holds the trinomial coefficients, and the layers sum to powers of 3.

```pycon
>>> c = ndplex(4, edges=3)
>>> print(c.as_tri()[2])
[[1 2 1 0]
 [2 2 0 0]
 [1 0 0 0]
 [0 0 0 0]]
>>> print(c.as_tri(sums=True))
[ 1  3  9 27]
```

The same works in any number of dimensions: `ndplex(5, edges=4)` is a 4-D array, and its `as_tri` is a 4-simplex.

## Large values

Node values grow quickly. With the default `int64`, the 2-D array is exact for nodes with `i + j <= 66`. If any node overflows, construction issues one `RuntimeWarning` naming the first node that did. For exact integers of any size, use `dtype=object`:

```pycon
>>> print(ndplex(70, dtype=object)[69, 69])
23623985175715118288974865541854103729000
```

When only a residue is needed, reduce inside `func` instead, as in the Sierpinski example above.

## Looking rows up in OEIS

`oeis` searches oeis.org for each row of an array and prints the best match. It sends one request per row, so please search a few rows at a time.

```python
from ndplex import ndplex, oeis

oeis(ndplex(5))
oeis(ndplex(9).as_tri(), trim=True, size=5)   # rows of the triangle, zeros trimmed
matches = oeis(ndplex(5), quiet=True)        # a list of (A-number, name) or None
```

The output has one line per row, for example `row 2: https://oeis.org/A000217 Triangular numbers: ...`. The names come from OEIS and can change. If oeis.org cannot be reached or refuses the request, the row's line says `lookup failed (...)`. Each request identifies itself to oeis.org as `ndplex/<version>`.

## Examples notebook

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/tedteske/ndplex/blob/master/notebooks/ndplex_examples.ipynb)

[`notebooks/ndplex_examples.ipynb`](https://github.com/tedteske/ndplex/blob/master/notebooks/ndplex_examples.ipynb) installs ndplex from PyPI and runs the examples from the original notebook: Pascal's triangle and tetrahedron, other edges and rules, diagonals and ratios, heatmaps and modular arithmetic, the simplex, duplex and triplex triangles, binomial-to-normal histograms, Fibonacci and Narayana's cows, a rental-rate model, and patterns among the primes. Open it in Colab with the badge above and choose Runtime → Run all.

## Plotting

From 0.1.0, plotting is left to the user, so `import ndplex` needs only NumPy. Working copies of the original notebook's `plot_ndplex` and `diag_as_hist`, fixed for current matplotlib, are in the helper cell of the [examples notebook](https://github.com/tedteske/ndplex/blob/master/notebooks/ndplex_examples.ipynb). They need only NumPy and matplotlib.

## Changes from the notebook

ndplex began as the first code cell of `ndplex_array.ipynb` (2019–2024). The package keeps the notebook's results except where a change is documented. The changes are listed in the [changelog](https://github.com/tedteske/ndplex/blob/master/CHANGELOG.md), with migration notes in [`docs/`](https://github.com/tedteske/ndplex/tree/master/docs). In brief: no import side effects, plotting left out, overflow reported, `arg_locs` outside the array read 0, `diag` ends where its moves leave the array, and `as_tri` layers are justified left in every dimension.

## Background and credits

ndplex is the original work of Ted Teske (2019–2024). A general source for it is Thomas M. Green, *The Simplex, Duplex and Pascal's Triangles: Relatives of Pascal's Triangle, with Excursions Into Hyperspace* (CreateSpace, 2015; ISBN 9781514677094).

The packaging, tests and audit (2026) were developed with assistance from Claude (Anthropic). [`ATTRIBUTION.md`](https://github.com/tedteske/ndplex/blob/master/ATTRIBUTION.md) sets out which work is whose, and the references.

## Citing

If you use ndplex in published work, please cite it. GitHub's "Cite this repository" button gives APA and BibTeX from [`CITATION.cff`](https://github.com/tedteske/ndplex/blob/master/CITATION.cff). Releases are archived on Zenodo: [10.5281/zenodo.24054477](https://doi.org/10.5281/zenodo.24054477) cites all versions (and resolves to the latest); each version also has its own DOI, listed on that record, for citing the exact release you used (0.1.0: [10.5281/zenodo.24054478](https://doi.org/10.5281/zenodo.24054478)).

## License

MIT. Copyright (c) 2019 Ted Teske.
