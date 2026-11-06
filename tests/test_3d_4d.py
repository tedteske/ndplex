"""
Suite B -- 3-D and 4-D arrays (Pascal's tetrahedron and the 4-simplex).

Values are the notebook's saved outputs ("First 3D examples", cells 46-63;
"The Special Case of func=lambda x:1", cells 163-181; "More than 2
dimensions", cells 270-271), plus multinomial property checks.
"""
import math

import numpy as np
import pytest
from numpy.testing import assert_array_equal

from _impl import ndplex
from primes import first_primes

P3_5 = [
    [[1, 1, 1, 1, 1],
     [1, 2, 3, 4, 5],
     [1, 3, 6, 10, 15],
     [1, 4, 10, 20, 35],
     [1, 5, 15, 35, 70]],
    [[1, 2, 3, 4, 5],
     [2, 6, 12, 20, 30],
     [3, 12, 30, 60, 105],
     [4, 20, 60, 140, 280],
     [5, 30, 105, 280, 630]],
    [[1, 3, 6, 10, 15],
     [3, 12, 30, 60, 105],
     [6, 30, 90, 210, 420],
     [10, 60, 210, 560, 1260],
     [15, 105, 420, 1260, 3150]],
    [[1, 4, 10, 20, 35],
     [4, 20, 60, 140, 280],
     [10, 60, 210, 560, 1260],
     [20, 140, 560, 1680, 4200],
     [35, 280, 1260, 4200, 11550]],
    [[1, 5, 15, 35, 70],
     [5, 30, 105, 280, 630],
     [15, 105, 420, 1260, 3150],
     [35, 280, 1260, 4200, 11550],
     [70, 630, 3150, 11550, 34650]],
]

TETRA_5 = [
    [[1, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0],
     [0, 0, 0, 0, 0]],
    [[1, 1, 0, 0, 0], [1, 0, 0, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0],
     [0, 0, 0, 0, 0]],
    [[1, 2, 1, 0, 0], [2, 2, 0, 0, 0], [1, 0, 0, 0, 0], [0, 0, 0, 0, 0],
     [0, 0, 0, 0, 0]],
    [[1, 3, 3, 1, 0], [3, 6, 3, 0, 0], [3, 3, 0, 0, 0], [1, 0, 0, 0, 0],
     [0, 0, 0, 0, 0]],
    [[1, 4, 6, 4, 1], [4, 12, 12, 4, 0], [6, 12, 6, 0, 0], [4, 4, 0, 0, 0],
     [1, 0, 0, 0, 0]],
]


def multinomial(*ks):
    out = math.factorial(sum(ks))
    for k in ks:
        out //= math.factorial(k)
    return out


@pytest.fixture(scope="module")
def p3():
    return ndplex(5, edges=3)


# --- 3-D ----------------------------------------------------------------------

def test_tetrahedron_array_values(p3):
    assert_array_equal(p3, P3_5)
    assert p3.shape == (5, 5, 5)
    assert_array_equal(p3.arg_locs, -np.eye(3, dtype=int))


def test_3d_nodes_are_trinomials():
    n = 8
    got = ndplex(n, edges=3)
    for i in range(n):
        for j in range(n):
            for k in range(n):
                assert got[i, j, k] == multinomial(i, j, k)


def test_3d_layer_0_is_pascal_rectangle(p3):
    assert_array_equal(p3[0], ndplex(5))


def test_oblong_numbers(p3):
    assert_array_equal(p3[1, 1, :], [2, 6, 12, 20, 30])
    assert_array_equal(p3.diag(loc=(1, 1, 0), move=(0, 0, 1)),
                       [2, 6, 12, 20, 30])


def test_3d_main_diagonal(p3):
    assert_array_equal(p3.diag(), [1, 6, 90, 1680, 34650])


def test_3d_diag_of_rows(p3):
    """loc of length 2 in 3-D: start at a row, return a 2-D slab."""
    assert_array_equal(p3.diag(loc=(0, 0), move=(1, 1)),
                       [[1, 1, 1, 1, 1],
                        [2, 6, 12, 20, 30],
                        [6, 30, 90, 210, 420],
                        [20, 140, 560, 1680, 4200],
                        [70, 630, 3150, 11550, 34650]])


def test_3d_diagonal_cross_section(p3):
    assert_array_equal(p3.diag(loc=(0, 0, 0), move=[(0, -1, 1), (1, 1, 0)]),
                       [[1, 0, 0, 0, 0],
                        [2, 2, 0, 0, 0],
                        [6, 12, 6, 0, 0],
                        [20, 60, 60, 20, 0],
                        [70, 280, 420, 280, 70]])


def test_3d_horizontal_cross_section_row_4(p3):
    assert_array_equal(p3.diag(loc=(0, 4, 0), move=[(0, -1, 1), (1, -1, 0)]),
                       TETRA_5[4])


def test_tetrahedron_via_as_tri(p3):
    assert_array_equal(p3.as_tri(0, 4), TETRA_5)
    assert_array_equal(p3.as_tri(), TETRA_5)


def test_layer_sums_are_powers_of_3(p3):
    assert_array_equal(p3.as_tri(0, 4, sums=True), [1, 3, 9, 27, 81])
    assert_array_equal(ndplex(12, edges=3).as_tri(sums=True), 3 ** np.arange(12))


def test_3d_as_tri_layers_are_trinomial_triangles():
    n = 7
    tet = ndplex(n, edges=3).as_tri()
    for r in range(n):
        for a in range(n):
            for b in range(n):
                want = multinomial(a, b, r - a - b) if a + b <= r else 0
                assert tet[r, a, b] == want


# --- 4-D ----------------------------------------------------------------------

def test_4d_nodes_are_multinomials():
    n = 5
    got = ndplex(n, edges=4)
    assert got.shape == (n,) * 4
    for idx in np.ndindex(got.shape):
        assert got[idx] == multinomial(*idx)


def test_4d_layer_sums_are_powers_of_4():
    """Extends the notebook's powers-of-2 and powers-of-3 pattern to 4-D."""
    assert_array_equal(ndplex(6, edges=4).as_tri(sums=True), 4 ** np.arange(6))


# --- func=lambda x: 1: triangular, tetrahedral and 4-simplex numbers ---------

def test_ones_2d_triangular_numbers():
    ones = ndplex(9, edges=2, func=lambda x: 1)
    assert_array_equal(ones, np.ones((9, 9), dtype=int))
    assert_array_equal(ones.as_tri(), np.tril(np.ones((9, 9), dtype=int)))
    assert_array_equal(ones.as_tri(sums=True).cumsum(-1),
                       [1, 3, 6, 10, 15, 21, 28, 36, 45])
    assert_array_equal(ndplex(9)[2], [1, 3, 6, 10, 15, 21, 28, 36, 45])


def test_ones_3d_tetrahedral_numbers():
    ones = ndplex(5, edges=3, func=lambda x: 1)
    assert_array_equal(ones, np.ones((5, 5, 5), dtype=int))
    tet = ones.as_tri()
    assert_array_equal(tet[4], [[1, 1, 1, 1, 1], [1, 1, 1, 1, 0],
                                [1, 1, 1, 0, 0], [1, 1, 0, 0, 0],
                                [1, 0, 0, 0, 0]])
    assert_array_equal(ones.as_tri(sums=True).cumsum(-1), [1, 4, 10, 20, 35])
    assert_array_equal(ndplex(5)[3], [1, 4, 10, 20, 35])


def test_ones_4d_simplex_numbers():
    ones = ndplex(5, edges=4, func=lambda x: 1)
    assert_array_equal(ones.as_tri(sums=True).cumsum(-1), [1, 5, 15, 35, 70])
    assert_array_equal(ndplex(5)[4], [1, 5, 15, 35, 70])


# --- 3-D with a prime edge ----------------------------------------------------

def test_3d_prime_edge():
    size = 10
    p = [1] + first_primes(size - 1)
    prime_xd = ndplex(size, (p, 1, 1))
    assert_array_equal(prime_xd.diag(),
                       [1, 8, 126, 2420, 50750, 1120896, 25611432, 599439984,
                        14284168470, 345153963440])
    assert_array_equal(prime_xd.as_tri(sums=True),
                       [1, 4, 13, 41, 125, 379, 1139, 3421, 10265, 30799])
