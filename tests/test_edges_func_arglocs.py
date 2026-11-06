"""
Suite C -- the edges, func and arg_locs parameters.

Values are the notebook's saved outputs ("The edges Parameter", cells
66-82; "The func and arg_locs Parameters", cells 86-104; "An oscillating
function", cells 112-114; "Geometry", cells 147-157; Fibonacci edges and
the golden ratio, cells 223 and 228; modular arithmetic, cells 132-140),
plus checks of edge orientation that the docstring leaves implicit.
"""
import math

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal

from _impl import ndplex


def odds(size):
    return np.arange(1, size + 1) * 2 - 1


def evens(size):
    return np.arange(1, size + 1) * 2


def fibonaccis(size):
    f = [1, 1]
    for i in range(2, size):
        f.append(f[i - 1] + f[i - 2])
    return f


# --- edges ------------------------------------------------------------------

def test_edge_orientation_2d():
    """edges[0] fills column 0, edges[1] fills row 0; where they meet (the
    origin) the last edge wins."""
    a = ndplex(4, edges=([10, 11, 12, 13], [20, 21, 22, 23]))
    assert_array_equal(a[:, 0], [20, 11, 12, 13])
    assert_array_equal(a[0, :], [20, 21, 22, 23])


def test_edge_orientation_3d():
    """In 3-D, edges[k] fills the line along axis k through the origin
    (the origin itself takes the last edge's first value)."""
    a = ndplex(3, edges=([10, 11, 12], [20, 21, 22], [30, 31, 32]))
    assert_array_equal(a[:, 0, 0], [30, 11, 12])
    assert_array_equal(a[0, :, 0], [30, 21, 22])
    assert_array_equal(a[0, 0, :], [30, 31, 32])


def test_counting_number_edges():
    c = np.arange(1, 10)
    assert_array_equal(ndplex(9, edges=(c, c)), [
        [1, 2, 3, 4, 5, 6, 7, 8, 9],
        [2, 4, 7, 11, 16, 22, 29, 37, 46],
        [3, 7, 14, 25, 41, 63, 92, 129, 175],
        [4, 11, 25, 50, 91, 154, 246, 375, 550],
        [5, 16, 41, 91, 182, 336, 582, 957, 1507],
        [6, 22, 63, 154, 336, 672, 1254, 2211, 3718],
        [7, 29, 92, 246, 582, 1254, 2508, 4719, 8437],
        [8, 37, 129, 375, 957, 2211, 4719, 9438, 17875],
        [9, 46, 175, 550, 1507, 3718, 8437, 17875, 35750]])


def test_counting_and_negative_edges():
    c = np.arange(9)
    assert_array_equal(ndplex(9, edges=(c, -c)), [
        [0, -1, -2, -3, -4, -5, -6, -7, -8],
        [1, 0, -2, -5, -9, -14, -20, -27, -35],
        [2, 2, 0, -5, -14, -28, -48, -75, -110],
        [3, 5, 5, 0, -14, -42, -90, -165, -275],
        [4, 9, 14, 14, 0, -42, -132, -297, -572],
        [5, 14, 28, 42, 42, 0, -132, -429, -1001],
        [6, 20, 48, 90, 132, 132, 0, -429, -1430],
        [7, 27, 75, 165, 297, 429, 429, 0, -1430],
        [8, 35, 110, 275, 572, 1001, 1430, 1430, 0]])


def test_zero_on_first_row_3d():
    assert_array_equal(ndplex(5, edges=(1, 1, 0))[0:2], [
        [[0, 0, 0, 0, 0],
         [1, 1, 1, 1, 1],
         [1, 2, 3, 4, 5],
         [1, 3, 6, 10, 15],
         [1, 4, 10, 20, 35]],
        [[1, 1, 1, 1, 1],
         [2, 4, 6, 8, 10],
         [3, 9, 18, 30, 45],
         [4, 16, 40, 80, 140],
         [5, 25, 75, 175, 350]]])


def test_two_on_row_0_gives_odds_and_squares():
    a = ndplex(9, edges=(1, 2))
    assert_array_equal(a[0], [2] * 9)
    assert_array_equal(a[1], odds(9))
    assert_array_equal(a[2], np.arange(1, 10) ** 2)
    assert_array_equal(a[8], [1, 10, 54, 210, 660, 1782, 4290, 9438, 19305])


def test_odds_on_row_0():
    a = ndplex(9, edges=(1, odds(9)))
    assert_array_equal(a[0], odds(9))
    assert_array_equal(a[1], np.arange(1, 10) ** 2)
    # square pyramidal numbers, then 4-dimensional pyramidal numbers
    assert_array_equal(a[2], [1, 5, 14, 30, 55, 91, 140, 204, 285])
    assert_array_equal(a[3], [1, 6, 20, 50, 105, 196, 336, 540, 825])
    assert_array_equal(a[8], [1, 11, 65, 275, 935, 2717, 7007, 16445, 35750])


def test_evens_and_odds_from_common_origin():
    odds0 = [0] + list(odds(8))
    evens0 = [0] + list(evens(8))
    a = ndplex(9, edges=(evens0, odds0))
    assert_array_equal(a[1], [2, 3, 6, 11, 18, 27, 38, 51, 66])
    assert_array_equal(a[:, 0], [0, 2, 4, 6, 8, 10, 12, 14, 16])
    assert_array_equal(a[8], [16, 73, 251, 725, 1859, 4367, 9581, 19877, 39325])


def test_fibonacci_edges():
    f = fibonaccis(9)
    a = ndplex(9, edges=(f, f))
    assert_array_equal(a[1], [1, 2, 4, 7, 12, 20, 33, 54, 88])
    assert_array_equal(a.diag(), [1, 2, 8, 30, 114, 436, 1676, 6468, 25040])
    assert_array_equal(a[8], [34, 88, 222, 540, 1260, 2818, 6052, 12520, 25040])


# --- func ---------------------------------------------------------------------

@pytest.mark.parametrize("func", [lambda x: sum(x), lambda x: x[0] + x[1], sum],
                         ids=["lambda-sum", "x0+x1", "builtin-sum"])
def test_equivalent_default_funcs(func):
    assert_array_equal(ndplex(5, func=func), ndplex(5))


def test_func_x0_plus_2x1():
    assert_array_equal(ndplex(5, func=lambda x: x[0] + x[1] * 2), [
        [1, 1, 1, 1, 1],
        [1, 3, 7, 15, 31],
        [1, 5, 17, 49, 129],
        [1, 7, 31, 111, 351],
        [1, 9, 49, 209, 769]])


def test_func_pythagorean_float():
    def f(x):
        return (x[0] ** 2 + x[1] ** 2) ** 0.5
    got = ndplex(5, func=f, dtype=float).round(3)
    assert_array_equal(got, [
        [1., 1., 1., 1., 1.],
        [1., 1.414, 1.732, 2., 2.236],
        [1., 1.732, 2.449, 3.162, 3.873],
        [1., 2., 3.162, 4.472, 5.916],
        [1., 2.236, 3.873, 5.916, 8.367]])
    assert_allclose(ndplex(9, func=f, dtype=float)[1], np.sqrt(np.arange(1, 10)))


def test_oscillating_func():
    func = lambda x: x[0] - x[1]
    p = ndplex(9, edges=2, dtype=int, func=func)
    assert_array_equal(p[1], [1, 0, 1, 0, 1, 0, 1, 0, 1])
    assert_array_equal(p[3], [1, -2, 4, -6, 9, -12, 16, -20, 25])
    assert_array_equal(p[8], [1, -7, 29, -91, 239, -553, 1163, -2269, 4166])


@pytest.mark.parametrize("n,sums", [
    (1, [1, 2, 4, 8, 16, 32, 64]),
    (2, [1, 3, 9, 27, 81, 243, 729]),
    (3, [1, 4, 16, 64, 256, 1024, 4096]),
])
def test_simplex_duplex_triplex_sums(n, sums):
    size = 7
    plex = ndplex(size, edges=(n ** np.arange(size), 1),
                  func=lambda x: n * x[0] + x[1])
    assert_array_equal(plex.as_tri(sums=True), sums)


def test_duplex_triangle():
    duplex = ndplex(7, edges=(2 ** np.arange(7), 1),
                    func=lambda x: 2 * x[0] + x[1])
    assert_array_equal(duplex.as_tri(), [
        [1, 0, 0, 0, 0, 0, 0],
        [2, 1, 0, 0, 0, 0, 0],
        [4, 4, 1, 0, 0, 0, 0],
        [8, 12, 6, 1, 0, 0, 0],
        [16, 32, 24, 8, 1, 0, 0],
        [32, 80, 80, 40, 10, 1, 0],
        [64, 192, 240, 160, 60, 12, 1]])
    # the cube: 8 vertices, 12 edges, 6 faces, 1 cube
    assert_array_equal(duplex.as_tri()[3], [8, 12, 6, 1, 0, 0, 0])


def test_triplex_triangle_base():
    triplex = ndplex(7, edges=(3 ** np.arange(7), 1),
                     func=lambda x: 3 * x[0] + x[1])
    assert_array_equal(triplex.as_tri()[6], [729, 1458, 1215, 540, 135, 18, 1])


def test_golden_ratio_from_ratio_func():
    size = 20
    func = lambda x: (x[0] + x[1]) / x[0]
    p2 = ndplex(size, edges=(1, range(1, size + 1)), func=func, dtype=float)
    y = p2.diag(loc=(0, 1), move=(1, 0))
    assert len(y) == size
    assert y[-1] == pytest.approx(1.618033985017358, rel=1e-15)
    assert y[-1] == pytest.approx((1 + 5 ** 0.5) / 2, abs=1e-8)


# --- arg_locs -----------------------------------------------------------------

def test_explicit_default_arg_locs():
    assert_array_equal(
        ndplex(5, arg_locs=[[-1, 0], [0, -1]], func=lambda x: x[0] + x[1]),
        ndplex(5))


def test_three_neighbour_arg_locs_centered_numbers():
    q = ndplex(5, arg_locs=[[-1, 0], [0, -1], [-1, -1]],
               func=lambda x: x[0] + x[1] + x[2])
    assert_array_equal(q, [
        [1, 1, 1, 1, 1],
        [1, 3, 5, 7, 9],
        [1, 5, 13, 25, 41],
        [1, 7, 25, 63, 129],
        [1, 9, 41, 129, 321]])


def test_arg_locs_none_multiplication_table():
    c = np.arange(1, 11)
    got = ndplex(10, edges=(c, c), arg_locs=[[None, 0], [0, None]],
                 func=lambda x: x[0] * x[1])
    assert_array_equal(got, np.outer(c, c))


def test_arg_locs_none_concave_surface():
    c = np.arange(-5, 5)
    z = lambda x: -x[0] ** 2 + -x[1] ** 2 + 100
    a = ndplex(10, edges=(c, c), arg_locs=[[None, 0], [0, None]], func=z)
    assert_array_equal(a[0], c)
    assert_array_equal(a[:, 0], c)
    assert_array_equal(a[1:, 1:], 100 - c[1:, None] ** 2 - c[None, 1:] ** 2)
    assert_array_equal(a[5], [0, 84, 91, 96, 99, 100, 99, 96, 91, 84])


# --- modular arithmetic (the heatmap examples) --------------------------------

@pytest.mark.filterwarnings("ignore:overflow encountered:RuntimeWarning")
def test_sierpinski_mod_2_matches_lucas():
    """Cell 132: C(i+j, i) is odd exactly when i & j == 0 (Lucas). Holds on
    the int64 array even past overflow, because int64 wraps modulo 2**64."""
    n = 100
    i, j = np.indices((n, n))
    assert_array_equal(ndplex(n) % 2, ((i & j) == 0).astype(int))


def test_mod_inside_func_is_exact():
    """Cell 138: putting the modulus in func gives exact residues."""
    n, d = 100, 5
    got = ndplex(n, dtype=np.int64, func=lambda x: (x[0] + x[1]) % d)
    want = [[math.comb(i + j, i) % d for j in range(n)] for i in range(n)]
    assert_array_equal(got, want)


def test_digit_sum_func_is_digital_root():
    """Cell 140: repeated digit sums give the digital root of C(i+j, i)."""
    def sum_digits(num):
        num = str(num)
        if len(num) < 2:
            return int(num)
        return sum_digits(sum(int(d) for d in num))
    n = 30
    got = ndplex(n, dtype=np.int64, func=lambda x: sum_digits(x[0] + x[1]))
    want = [[1 + (math.comb(i + j, i) - 1) % 9 for j in range(n)]
            for i in range(n)]
    assert_array_equal(got, want)
