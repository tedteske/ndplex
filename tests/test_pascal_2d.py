"""
Suite A -- default 2-D ndplex (Pascal's rectangle), diag and as_tri.

Values are the notebook's saved outputs ("First 2D examples", cells 6-30 of
ndplex_array.ipynb at commit 7560854), plus property checks against
math.comb that extend them to other sizes.
"""
import math

import numpy as np
import pytest
from numpy.testing import assert_array_equal

from _impl import ndplex

PASCAL_9 = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 3, 6, 10, 15, 21, 28, 36, 45],
    [1, 4, 10, 20, 35, 56, 84, 120, 165],
    [1, 5, 15, 35, 70, 126, 210, 330, 495],
    [1, 6, 21, 56, 126, 252, 462, 792, 1287],
    [1, 7, 28, 84, 210, 462, 924, 1716, 3003],
    [1, 8, 36, 120, 330, 792, 1716, 3432, 6435],
    [1, 9, 45, 165, 495, 1287, 3003, 6435, 12870],
]

TRIANGLE_9 = [
    [1, 0, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 0, 0, 0, 0, 0, 0, 0],
    [1, 2, 1, 0, 0, 0, 0, 0, 0],
    [1, 3, 3, 1, 0, 0, 0, 0, 0],
    [1, 4, 6, 4, 1, 0, 0, 0, 0],
    [1, 5, 10, 10, 5, 1, 0, 0, 0],
    [1, 6, 15, 20, 15, 6, 1, 0, 0],
    [1, 7, 21, 35, 35, 21, 7, 1, 0],
    [1, 8, 28, 56, 70, 56, 28, 8, 1],
]


@pytest.fixture(scope="module")
def p():
    return ndplex(9)


# --- the array itself -------------------------------------------------------

def test_default_rectangle_values(p):
    assert_array_equal(p, PASCAL_9)
    assert p.shape == (9, 9)
    # np.int64 on every platform (Phase 2, C7). Until Phase 3 this line was
    # `== np.dtype(int)`, the notebook's platform default, which equals
    # int64 except on Windows with NumPy < 2 (docs/phase3_ci.md, P3).
    assert p.dtype == np.int64


def test_default_attributes(p):
    assert p.nrows == 9
    assert p.edges == (1, 1)
    assert_array_equal(p.arg_locs, [[-1, 0], [0, -1]])


@pytest.mark.parametrize("n", [1, 2, 3, 10, 30])
def test_nodes_are_binomials(n):
    """Node [i, j] of the default 2-D array is C(i + j, i)."""
    want = [[math.comb(i + j, i) for j in range(n)] for i in range(n)]
    assert_array_equal(ndplex(n), want)


def test_edges_int_2_is_default(p):
    """`edges=2` means two edges of ones (the notebook uses both forms)."""
    assert_array_equal(ndplex(9, edges=2), p)


def test_float_dtype_same_values():
    assert_array_equal(ndplex(9, dtype=float), PASCAL_9)
    assert ndplex(9, dtype=float).dtype == np.float64


# --- slicing and diag ---------------------------------------------------------

def test_counting_numbers_row_and_column(p):
    assert_array_equal(p[1], range(1, 10))
    assert_array_equal(p[:, 1], range(1, 10))
    assert_array_equal(p.diag(loc=(1, 0), move=(0, 1)), range(1, 10))


def test_triangular_numbers_column_2(p):
    assert_array_equal(p.diag(loc=(0, 2), move=(1, 0)),
                       [1, 3, 6, 10, 15, 21, 28, 36, 45])


def test_diagonal_4_is_row_of_triangle(p):
    assert_array_equal(p.diag(loc=(4, 0), move=(-1, 1)), [1, 4, 6, 4, 1])


@pytest.mark.parametrize("k", range(9))
def test_antidiagonal_k_is_binomial_row(p, k):
    assert_array_equal(p.diag(loc=(k, 0), move=(-1, 1)),
                       [math.comb(k, j) for j in range(k + 1)])


def test_main_diagonal_is_central_binomials(p):
    assert_array_equal(p.diag(),
                       [1, 2, 6, 20, 70, 252, 924, 3432, 12870])


def test_diag_returns_plain_ndarray(p):
    assert type(p.diag()) is np.ndarray


# --- the triangle -------------------------------------------------------------

def test_triangle_via_diag(p):
    assert_array_equal(p.diag(move=[(-1, 1), (1, 0)]), TRIANGLE_9)


def test_triangle_via_as_tri(p):
    assert_array_equal(p.as_tri(), TRIANGLE_9)


def test_triangle_rows_without_zeros(p):
    rows = [list(np.trim_zeros(r)) for r in p.as_tri()]
    assert rows == [[math.comb(r, c) for c in range(r + 1)] for r in range(9)]


def test_row_sums_are_powers_of_2(p):
    want = [1, 2, 4, 8, 16, 32, 64, 128, 256]
    assert_array_equal(p.diag(move=[(-1, 1), (1, 0)], sum_axis=1), want)
    assert_array_equal(p.as_tri(sums=True), want)


@pytest.mark.parametrize("n", [2, 5, 20])
def test_row_sums_powers_of_2_other_sizes(n):
    assert_array_equal(ndplex(n).as_tri(sums=True), 2 ** np.arange(n))


def test_as_tri_start_end():
    """as_tri(start, end) keeps rows start..end inclusive, width end + 1."""
    got = ndplex(6).as_tri(2, 4)
    assert_array_equal(got, [[1, 2, 1, 0, 0],
                             [1, 3, 3, 1, 0],
                             [1, 4, 6, 4, 1]])
    assert_array_equal(ndplex(6).as_tri(2, 4, sums=True), [4, 8, 16])


def test_as_tri_returns_plain_ndarray(p):
    assert type(p.as_tri()) is np.ndarray
