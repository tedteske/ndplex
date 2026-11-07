"""
Suite H -- behaviour that could differ by platform or NumPy version (Phase 3).

Phase 2 tested Linux only. Phase 3 runs the suite on Linux, macOS and
Windows, on NumPy 1.23.5 (the declared minimum) and the latest NumPy. The
findings are in docs/phase3_ci.md.

P1 (fixed, C12). Integer overflow went unreported for dtypes narrower than
the platform's default int on NumPy < 2: ndplex(40, dtype=np.int32) gave the
same wrapped values as on NumPy 2 but no warning, on Linux and macOS. The
default func=sum starts from the Python int 0, and on NumPy < 2 that
promotes the running total to the platform's default int (int64 there), so
numpy saw no overflow; the value was then wrapped silently on assignment.
Separately, a func returning an integer too large for the dtype was wrapped
silently on NumPy < 2 but raised OverflowError on NumPy 2. Construction now
checks every integer func returns against the dtype's range: out-of-range
values are wrapped modulo 2**bits and reported in the one overflow warning,
on every platform and NumPy version.

P2 (documented, no change). dtype=int means numpy's default integer, which
is int32 on Windows with NumPy < 2 and int64 elsewhere. The default dtype is
np.int64 everywhere (Phase 2, C7); dtype=int is the user's choice of the
platform type, and overflow in it is now reported (P1).
"""
import math
import warnings

import numpy as np
import pytest
from numpy.testing import assert_array_equal

from _impl import ndplex


def _build(*args, **kwargs):
    """Construct, returning (array, list of warnings)."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        p = ndplex(*args, **kwargs)
    return p, w


def _wrap(values, dtype):
    """Exact integers wrapped into dtype's range (two's complement)."""
    info = np.iinfo(dtype)
    low, span = int(info.min), int(info.max) - int(info.min) + 1
    return np.vectorize(lambda v: (v - low) % span + low, otypes=[object])(values)


def _pascal(n):
    return np.array([[math.comb(i + j, i) for j in range(n)] for i in range(n)],
                    dtype=object)


def _first_wrong(got, exact):
    for node in np.ndindex(got.shape):
        if got[node] != exact[node]:
            return node
    return None


# --- P1 overflow in integer dtypes of every width -------------------------------

@pytest.mark.parametrize("dtype,first", [
    (np.int8, (2, 15)), (np.int16, (4, 28)), (np.int32, (10, 34)),
    (np.int64, (29, 39)), (np.uint8, (2, 22)), (np.uint16, (4, 33)),
    (np.uint32, (10, 37)),
])
def test_overflow_warns_for_every_integer_dtype(dtype, first):
    """P1. Phase 3: fixed (C12). On NumPy < 2 the narrow dtypes gave these
    values with no warning. The values are unchanged (wrapped modulo
    2**bits, as numpy wraps them); the warning is new there.
    Migration: none for results."""
    n = 40
    p, w = _build(n, dtype=dtype)
    assert p.dtype == dtype
    exact = _pascal(n)
    got = p.astype(object)
    assert_array_equal(got, _wrap(exact, dtype))
    assert _first_wrong(got, exact) == first
    assert [x.category for x in w] == [RuntimeWarning]
    assert str(w[0].message).startswith(
        f"ndplex: node values overflowed {np.dtype(dtype)} from node {first} on")


def test_overflow_warns_in_3d_narrow_dtype():
    p, w = _build(12, edges=3, dtype=np.int16)
    exact = ndplex(12, edges=3, dtype=object)
    got = p.astype(object)
    assert_array_equal(got, _wrap(exact, np.int16))
    first = _first_wrong(got, exact)
    assert len(w) == 1 and f"overflowed int16 from node {first} on" in str(w[0].message)


def _widen(x):
    """A func whose result is np.int64 whatever the array's dtype."""
    return np.int64(x[0]) + np.int64(x[1])


@pytest.mark.parametrize("edges,value,warns", [
    ((127, 0), 127, False), ((127, 1), -128, True),
    ((-128, 0), -128, False), ((-128, -1), 127, True),
    ((100, 100), -56, True),
])
def test_value_wider_than_dtype_is_wrapped_and_reported(edges, value, warns):
    """P1. Phase 3: fixed (C12). A func returning an integer outside the
    dtype's range: NumPy < 2 wrapped it silently, NumPy 2 raised
    OverflowError. Now both wrap it and warn; the range ends are inclusive.
    Migration: on NumPy 2, code that caught OverflowError from construction
    gets a RuntimeWarning instead (catch it with warnings.catch_warnings
    and simplefilter("error") to keep failing)."""
    p, w = _build(2, edges=edges, dtype=np.int8, func=_widen)
    assert p[1, 1] == value and p.dtype == np.int8
    assert len(w) == int(warns)
    if warns:
        assert "overflowed int8 from node (1, 1) on" in str(w[0].message)


def test_python_ints_beyond_int64_are_wrapped():
    """P1. Phase 3: fixed (C12). Was OverflowError on every NumPy version."""
    p, w = _build(3, func=lambda x: int(x[0]) + int(x[1]) + 2 ** 64)
    assert_array_equal(p, ndplex(3))
    assert len(w) == 1 and "from node (1, 1) on" in str(w[0].message)
    p, w = _build(3, dtype=np.uint8, func=lambda x: int(x[0]) - 300)
    assert p[1, 1] == (1 - 300) % 256 and len(w) == 1


def test_overflow_check_keeps_later_values_consistent():
    """Every out-of-range value is wrapped, not only the first: nodes after
    the first overflow are computed from wrapped values, as numpy's own
    arithmetic would compute them."""
    p, w = _build(6, edges=(np.arange(100, 106), 1), dtype=np.int8, func=_widen)
    ref = np.zeros((6, 6), dtype=object)
    ref[:, 0], ref[0, :] = range(100, 106), 1
    ref[0, 0] = 1
    for i in range(1, 6):
        for j in range(1, 6):
            ref[i, j] = _wrap(np.array([ref[i - 1, j] + ref[i, j - 1]]), np.int8)[0]
    assert_array_equal(p.astype(object), ref)
    assert len(w) == 1


# --- no false alarms ---------------------------------------------------------------

def test_no_overflow_warning_when_values_fit_narrow_dtypes():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert ndplex(5, dtype=np.int8).max() == 70          # C(8, 4)
        assert ndplex(6, dtype=np.uint8).max() == 252        # C(10, 5)
        assert ndplex(9, dtype=np.int16).max() == 12870      # C(16, 8)
        assert ndplex(17, dtype=np.int32).max() == 601080390  # C(32, 16)
        # int8, func keeping values small
        ndplex(30, dtype=np.int8, func=lambda x: (x[0] + x[1]) % 7)


def test_truncation_is_not_overflow():
    """A float from func stored in an integer array is truncated by numpy;
    that is not reported as overflow."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        p = ndplex(6, func=lambda x: sum(x) / 2)
    assert p.dtype == np.int64 and p[5, 5] == 1


@pytest.mark.parametrize("dtype", [bool, np.float32, float, object])
def test_non_integer_dtypes_are_not_range_checked(dtype):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        p = ndplex(6, dtype=dtype)
    assert p.dtype == dtype


# --- P2 dtype=int is numpy's default int -------------------------------------------

def test_dtype_int_is_numpys_default_int():
    """P2. dtype=int is numpy's default integer: int32 on Windows with
    NumPy < 2, int64 elsewhere. The default dtype is int64 everywhere."""
    assert ndplex(3, dtype=int).dtype == np.dtype(int)
    assert ndplex(3).dtype == np.int64
    p, w = _build(40, dtype=int)
    assert len(w) == 1 and f"overflowed {np.dtype(int)} from node" in str(w[0].message)
    assert_array_equal(p.astype(object), _wrap(_pascal(40), np.dtype(int)))
