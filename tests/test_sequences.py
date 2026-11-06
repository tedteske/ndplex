"""
Suite D -- sequences read off diagonals, ratios, and the worked applications.

Values are the notebook's saved outputs ("Fibonacci Numbers, Cows, and
Population Growth", cells 203-217; "Adjacent Diagonal Number Ratios", cells
116-125; "Moving Costs, Turnover, and Rental Rates", cell 230; "Searching
for Patterns among the Primes", cells 236-268 and 274), with the primes
from tests/primes.py instead of the notebook's download.
"""
import math

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_array_equal

from _impl import ndplex
from primes import first_primes


def fibonaccis(size):
    f = [1, 1]
    for i in range(2, size):
        f.append(f[i - 1] + f[i - 2])
    return f


def narayana(size):
    a = [1, 1, 1]
    for _ in range(3, size):
        a.append(a[-1] + a[-3])
    return a[:size]


# --- Fibonacci and Narayana ---------------------------------------------------

def test_steep_diagonals():
    p = ndplex(9)
    assert_array_equal(p.diag(move=[(-2, 1), (1, 0)], sum_axis=None), [
        [1, 0, 0, 0, 0],
        [1, 0, 0, 0, 0],
        [1, 1, 0, 0, 0],
        [1, 2, 0, 0, 0],
        [1, 3, 1, 0, 0],
        [1, 4, 3, 0, 0],
        [1, 5, 6, 1, 0],
        [1, 6, 10, 4, 0],
        [1, 7, 15, 10, 1]])


def test_fibonacci_from_diagonal_sums():
    fibs = ndplex(9).diag(move=[(-2, 1), (1, 0)], sum_axis=1)
    assert_array_equal(fibs, [1, 1, 2, 3, 5, 8, 13, 21, 34])


@pytest.mark.filterwarnings("ignore:overflow encountered:RuntimeWarning")
def test_fibonacci_50_and_golden_ratio():
    """ndplex(50) overflows int64 in its far corner (audit F5), but the
    nodes on these diagonals stay small, so the sums are exact."""
    fibs = ndplex(50).diag(move=[(-2, 1), (1, 0)], sum_axis=1)
    assert [int(f) for f in fibs] == fibonaccis(50)
    assert fibs[-1] / fibs[-2] == pytest.approx(1.618033988749895, rel=1e-15)


@pytest.mark.filterwarnings("ignore:overflow encountered:RuntimeWarning")
def test_narayana_cows():
    p = ndplex(9)
    assert_array_equal(p.diag(move=[(-3, 1), (1, 0)], sum_axis=1),
                       [1, 1, 1, 2, 3, 4, 6, 9, 13])
    cows = ndplex(50).diag(move=[(-3, 1), (1, 0)], sum_axis=1)
    assert [int(c) for c in cows] == narayana(50)
    year, lifespan = 20, 6
    assert cows[year] == 1278
    cow_pop2 = cows[lifespan:] - cows[:-lifespan]
    assert cow_pop2[year - lifespan] == 1149


def test_increasing_slope_table():
    size = 10
    d = ndplex(size)
    b = np.zeros(size, int)
    for i in range(1, size + 1):
        b = np.append(b, d.diag(move=[(-i, 1), (1, 0)], sum_axis=1))
    b = np.trim_zeros(b).reshape(size, -1)
    assert_array_equal(b, [
        [1, 2, 4, 8, 16, 32, 64, 128, 256, 512],
        [1, 1, 2, 3, 5, 8, 13, 21, 34, 55],
        [1, 1, 1, 2, 3, 4, 6, 9, 13, 19],
        [1, 1, 1, 1, 2, 3, 4, 5, 7, 10],
        [1, 1, 1, 1, 1, 2, 3, 4, 5, 6],
        [1, 1, 1, 1, 1, 1, 2, 3, 4, 5],
        [1, 1, 1, 1, 1, 1, 1, 2, 3, 4],
        [1, 1, 1, 1, 1, 1, 1, 1, 2, 3],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 2],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]])


def test_base_of_triangle_by_slope():
    """Cell 221 histograms these diagonals: node (19 - s*k, k) = C(19-(s-1)k, k)."""
    p = ndplex(20, edges=2, dtype=float)
    assert_array_equal(p.diag(loc=(19, 0), move=(-1, 1)),
                       [math.comb(19, k) for k in range(20)])
    assert_array_equal(p.diag(loc=(19, 0), move=(-2, 1)),
                       [1, 18, 136, 560, 1365, 2002, 1716, 792, 165, 10])


# --- adjacent ratios ----------------------------------------------------------

def ratios(g):
    return g[1:] / g[:-1]


@pytest.mark.parametrize("edges,first5,last", [
    ((1, 1), [2., 3., 3.33333333, 3.5, 3.6], 3.9797979797979797),
    ((1, 2), [1.5, 3., 3.33333333, 3.5, 3.6], 3.9797979797979797),
    ((np.arange(100)[::-1], np.arange(100)),
     [np.inf, 3., 3.33333333, 3.5, 3.6], 3.97979797979798),
], ids=["standard", "edges-1-2", "opposite-edges"])
def test_main_diagonal_ratios_tend_to_4(edges, first5, last):
    with np.errstate(divide="ignore"):
        r = ratios(ndplex(100, edges=edges, dtype=float).diag())
    assert_allclose(r[:5], first5, rtol=1e-8)
    assert r[-1] == pytest.approx(last, rel=1e-14)


def test_ratio_with_counting_edge():
    with np.errstate(divide="ignore"):
        r = ratios(ndplex(100, edges=(1, np.arange(100)), dtype=float).diag())
    assert_allclose(r[:5], [np.inf, 3.5, 3.57142857, 3.64, 3.69230769], rtol=1e-8)
    assert r[-1] == pytest.approx(3.9800677966101694, rel=1e-14)


def test_ratio_with_other_func_tends_to_8():
    func = lambda x: x[0] + x[1] * 2
    r = ratios(ndplex(100, edges=(1, 1), func=func, dtype=float).diag())
    assert_allclose(r[:5], [3., 5.66666667, 6.52941176, 6.92792793, 7.15604681],
                    rtol=1e-8)
    assert r[-1] == pytest.approx(7.959504291616377, rel=1e-14)


# --- rental rates -------------------------------------------------------------

def test_average_rental_rate():
    size = 50
    turnover = 0.4
    renewals = 1 - turnover
    moving_costs = 600
    market = 450
    renewal = market + moving_costs / 12.0
    f = lambda x: x[1] * renewals + x[0] * turnover
    rates = ndplex(size, edges=[renewal, market], func=f, dtype=float).diag(
        loc=[size - 1, 0], move=[-1, 1])
    f2 = lambda x: x[1] * renewals / turnover + x[0]
    weights = ndplex(size, func=f2, dtype=float).diag(loc=[size - 1, 0],
                                                      move=[-1, 1])
    rates, weights = zip(*sorted(zip(rates, weights)))
    assert np.average(rates, weights=weights).round(2) == 475.96


# --- primes -------------------------------------------------------------------

def test_primes_on_row_0():
    p = first_primes(8)
    a = ndplex(8, edges=(1, p))
    assert_array_equal(a[0], [2, 3, 5, 7, 11, 13, 17, 19])
    assert_array_equal(a[1], [1, 4, 9, 16, 27, 40, 57, 76])
    assert_array_equal(a[7], [1, 10, 54, 210, 662, 1798, 4364, 9694])
    b = ndplex(8, edges=(2, p))
    assert_array_equal(b[7], [2, 17, 82, 294, 872, 2260, 5288, 11410])


def test_primes_starting_with_1():
    p = [1] + first_primes(7)
    m = ndplex(8, edges=(1, p), arg_locs=[[-1, 0], [0, -1]])
    assert_array_equal(m[1], [1, 3, 6, 11, 18, 29, 42, 59])
    assert_array_equal(m.diag(), [1, 3, 10, 36, 132, 492, 1850, 7004])
    assert_array_equal(m.as_tri(sums=True), [1, 3, 7, 16, 34, 72, 146, 296])


def test_primes_on_both_edges():
    p = first_primes(9)
    m = ndplex(9, edges=(p, p))
    assert_array_equal(m.diag(), [2, 6, 22, 80, 298, 1116, 4208, 15956, 60794])
    assert_array_equal(m.as_tri(sums=True),
                       [2, 6, 16, 36, 80, 164, 336, 676, 1360])
    p1 = [1] + first_primes(8)
    m1 = ndplex(9, edges=(p1, p1))
    assert_array_equal(m1.diag(), [1, 4, 14, 52, 194, 732, 2776, 10576, 40450])
    assert_array_equal(m1.as_tri(sums=True),
                       [1, 4, 10, 24, 52, 112, 228, 464, 932])
    assert_array_equal(m1[1], [2, 4, 7, 12, 19, 30, 43, 60, 79])


def test_prime_difference_matrix_two_ways():
    size = 9
    p = first_primes(size)
    p1 = [1] + first_primes(size - 1)
    m2 = ndplex(size, edges=(np.arange(size) + 2, p))
    m1 = ndplex(size, edges=(np.arange(size) + 1, p1))
    diff = m2 - m1
    assert_array_equal(np.diagonal(diff),
                       [1, 2, 7, 24, 87, 318, 1178, 4406, 16607])
    diff2 = ndplex(size, edges=(1, np.asarray(p) - np.asarray(p1)))
    assert_array_equal(diff, diff2)
    assert_array_equal(diff2[0], [1, 1, 2, 2, 4, 2, 4, 2, 4])
    assert_array_equal(diff2[8], [1, 9, 46, 174, 542, 1468, 3572, 7978, 16607])


def test_primes_with_duplex_rule():
    f = lambda x: 2 * x[0] + x[1]
    a = ndplex(7, edges=(first_primes(7), 2), func=f)
    assert_array_equal(a[6], [17, 447, 2297, 7719, 20609, 47343, 97641])
    p = [1] + first_primes(6)
    b = ndplex(7, edges=(p, 1), func=f)
    assert_array_equal(b[6], [13, 279, 1373, 4503, 11821, 26807, 54717])
    c = ndplex(7, edges=(p, np.arange(7) + 1), func=f)
    assert_array_equal(c[6], [13, 343, 1885, 6807, 19501, 47927, 105405])


def test_prime_matrix_big_ratios():
    p = first_primes(100)
    d = ndplex(100, edges=(p, p), dtype=float).diag(loc=(0, 0), move=(1, 1))
    r = ratios(d)
    assert_allclose(r[:5], [3., 3.66666667, 3.63636364, 3.725, 3.74496644],
                    rtol=1e-8)
    assert r[-1] == pytest.approx(3.9802421517818907, rel=1e-14)
