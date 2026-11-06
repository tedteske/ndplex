"""
Suite G -- known issues found by the Phase 1 audit (docs/phase1_audit.md),
and how the package resolves them (docs/phase2_package.md).

Each test is tied to a finding number in the audit note. In Phase 1 the
tests of the intended behaviour were `xfail(strict=True)` and the tests of
behaviour awaiting a decision were named `test_current_*`. Phase 2 fixed the
findings: each xfail marker came off in the commit that made its test pass,
and each `test_current_*` test whose behaviour changed was rewritten to the
new behaviour, with a migration note in docs/phase2_package.md (the "Phase
2" line in each docstring says which). `test_current_*` names that remain
pin behaviour that did not change.
"""
import copy
import math
import pickle
import re
import subprocess
import sys
import warnings

import numpy as np
import pytest
from numpy.testing import assert_array_equal

from _impl import IMPORT_IN_SUBPROCESS, ndplex, oeis

OVERFLOW_WARNING = "ignore:ndplex. node values overflowed:RuntimeWarning"


# --- F1 import-time side effects ----------------------------------------------

def _import_in_fresh_process(code, before=""):
    # numpy is imported first: its own import adds warning filters.
    prog = ("import sys, warnings\nimport numpy\n" + before
            + "filters_before = list(warnings.filters)\n"
            + IMPORT_IN_SUBPROCESS + code)
    return subprocess.run([sys.executable, "-c", prog], capture_output=True,
                          text=True, check=True).stdout.strip()


def test_import_leaves_warning_filters_alone():
    """F1. Phase 2: fixed (C1)."""
    out = _import_in_fresh_process(
        "print(list(warnings.filters) == filters_before)")
    assert out == "True"


def test_import_leaves_matplotlib_style_alone():
    """F1. Phase 2: fixed (C1); the package no longer touches matplotlib."""
    pytest.importorskip("matplotlib")
    out = _import_in_fresh_process(
        "print(mpl.rcParams['axes.facecolor'] == face)",
        before="import matplotlib as mpl; mpl.use('Agg')\n"
               "face = mpl.rcParams['axes.facecolor']\n")
    assert out == "True"


def test_import_needs_only_numpy():
    """F2. Phase 2: fixed (C2). Plotting left the package (decision D8 as
    revised: plotting is left to the user); oeis uses the standard library
    and is loaded on first use."""
    out = _import_in_fresh_process(
        "print(sorted(k for k in ('scipy', 'seaborn', 'requests', 'pandas', "
        "'matplotlib', 'ndplex._oeis') if k in sys.modules))")
    assert out == "[]"


# --- F4 ndarray subclass ---------------------------------------------------------

def test_diag_works_on_a_slice():
    """F4. Phase 2: fixed (C4); diag reads the shape, not a stored nrows."""
    assert_array_equal(ndplex(5)[1:].diag(), [1, 3, 10, 35])


def test_diag_works_after_arithmetic():
    """F4. Phase 2: fixed (C4)."""
    assert_array_equal((ndplex(4) * 2).diag(), [2, 4, 12, 40])


def test_pickle_round_trip_keeps_methods_working():
    """F4. Phase 2: fixed (C4)."""
    q = pickle.loads(pickle.dumps(ndplex(4)))
    assert_array_equal(q.diag(), [1, 2, 6, 20])
    assert q.edges == (1, 1) and q.func is sum
    assert_array_equal(q.arg_locs, [[-1, 0], [0, -1]])


def test_pickle_with_a_lambda_func_still_works():
    """F4. Phase 2 (new): the attributes are now pickled, so a func that
    cannot be pickled (a lambda) comes back as None instead of breaking
    pickling, which worked in the notebook."""
    p = ndplex(4, func=lambda x: x[0] + 2 * x[1])
    q = pickle.loads(pickle.dumps(p))
    assert_array_equal(q, p)
    assert q.func is None and q.edges == (1, 1)


def test_copies_and_slices_keep_the_record():
    """F4. Phase 2: edges, func and arg_locs travel with views and copies;
    nrows comes from the shape (None when the sides differ)."""
    p = ndplex(5, edges=([1, 2, 3, 4, 5], 1))
    for q in (p.copy(), copy.deepcopy(p), p.view(), p[1:], p.T, p + 1):
        assert q.edges is p.edges and q.func is sum
        assert_array_equal(q.arg_locs, [[-1, 0], [0, -1]])
    assert p.nrows == 5 and p[1:3, 1:3].nrows == 2
    assert p[1:].nrows is None and p[1].nrows == 5
    assert np.zeros((3, 3)).view(ndplex).edges is None


def test_result_types():
    """F4. Phase 2: changed (C4). Slices and arithmetic stay ndplex, as
    before; reductions now return plain scalars (they were 0-d ndplex
    arrays, printed as ndplex(12870)).
    Migration: none for values; np.max(p) prints as np.int64(70)."""
    p = ndplex(5)
    assert type(p[1]) is type(p)
    assert type(p + 1) is type(p)
    assert type(p == p) is type(p)
    assert type(p.T) is type(p)
    assert type(p.sum()) is np.int64 and p.sum() == 251
    assert type(np.max(p)) is np.int64 and np.max(p) == 70
    assert type(ndplex(4, dtype=float).round(1)) is np.ndarray
    assert type(p.diag()) is np.ndarray
    assert type(p.as_tri()) is np.ndarray


# --- F5 integer overflow ---------------------------------------------------------

def _first_wrong_in_generation_order(got, exact):
    for node in np.ndindex(got.shape):
        if got[node] != exact[node]:
            return node
    return None


def test_int64_overflow_wraps_after_66_and_warns_once():
    """F5. Phase 2: changed (C3, decision D3a). The values are unchanged
    (wrapped modulo 2**64), but construction now issues one RuntimeWarning
    naming the first node that overflowed, instead of numpy's per-operation
    warnings, which the notebook's import silenced.
    Migration: none for results; silence the warning, or use dtype=object,
    for arrays that overflow on purpose (Sierpinski mod 2 and mod 4)."""
    n = 70
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        p = ndplex(n)
    assert len(w) == 1 and w[0].category is RuntimeWarning
    got = p.astype(object)
    exact = np.array([[math.comb(i + j, i) for j in range(n)] for i in range(n)],
                     dtype=object)
    wrong = got != exact
    i, j = np.nonzero(wrong)
    assert (i + j).min() == 67  # every node with i + j <= 66 is exact
    first = _first_wrong_in_generation_order(got, exact)
    assert str(w[0].message) == (
        f"ndplex: node values overflowed int64 from node {first} on (in "
        "generation order); that node and those computed from it are wrong. "
        "Use dtype=object for exact integers, or reduce inside func (e.g. a "
        "modulus).")
    # The warning points at the caller's line, as numpy's own warnings do.
    assert w[0].filename == __file__
    # wrapping is modulo 2**64, so residues mod powers of 2 survive ...
    assert ((got % 8) == (exact % 8)).all()
    # ... and others do not (the notebook's "divisor 5" heatmap)
    assert not ((got % 5) == (exact % 5)).all()


def test_overflow_warns_when_warnings_are_not_silenced():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        ndplex(70)
    assert any("overflow" in str(x.message) for x in w)


def test_no_overflow_warning_when_values_fit():
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        ndplex(34)                       # largest node C(66, 33) fits
        ndplex(15, edges=3)              # i + j + k <= 42: fits
        ndplex(100, dtype=object)
        ndplex(50, func=lambda x: (x[0] + x[1]) % 5)  # modulus in func


def test_overflow_names_first_node_in_3d():
    with pytest.warns(RuntimeWarning, match="overflowed int64") as w:
        p = ndplex(16, edges=3)
    exact = ndplex(16, edges=3, dtype=object)
    first = _first_wrong_in_generation_order(p.astype(object), exact)
    assert sum(first) >= 44                 # 3-D is exact up to i + j + k = 43
    wrong = np.argwhere(p.astype(object) != exact)
    assert wrong.sum(axis=1).min() == 44
    assert f"from node {first} on" in str(w[0].message)


def test_float_overflow_also_warns():
    with pytest.warns(RuntimeWarning, match="overflowed float64"):
        p = ndplex(4, edges=(1e308, 1e308), dtype=float)
    assert np.isinf(p[1, 1])


def test_object_dtype_is_exact():
    """dtype=object stores Python ints, so construction and diag are exact."""
    n = 100
    got = ndplex(n, dtype=object)
    assert got[n - 1, n - 1] == math.comb(2 * n - 2, n - 1)
    assert got.diag()[-1] == math.comb(2 * n - 2, n - 1)
    assert ndplex(60, dtype=object).as_tri(sums=True)[-1] == 2 ** 59


def test_object_dtype_sums_past_int64():
    """N12. Phase 2: fixed (C3); padding in diag and as_tri is now Python
    int zeros for dtype=object."""
    assert ndplex(100, dtype=object).as_tri(sums=True)[-1] == 2 ** 99
    big = ndplex(100, dtype=object).diag(loc=(99, 0), move=(-1, 1))
    assert sum(big) == 2 ** 99
    assert ndplex(100, dtype=object).diag(
        move=[(-1, 1), (1, 0)], sum_axis=1)[-1] == 2 ** 99
    assert ndplex(40, edges=3, dtype=object).as_tri(sums=True)[-1] == 3 ** 39


@pytest.mark.filterwarnings(OVERFLOW_WARNING)
def test_current_fibonacci_mod_7_heatmap_is_partly_overflowed():
    """Notebook cell 226 heatmaps ndplex(50, edges=(fib, 1)) % 7. Its lower
    right part (i + j >= 66) is overflow, not pattern. Unchanged in Phase 2,
    except that construction now warns."""
    f = [1, 1]
    for _ in range(48):
        f.append(f[-1] + f[-2])
    with pytest.warns(RuntimeWarning, match="overflowed"):
        a = ndplex(50, edges=(f, 1)) % 7
    exact = ndplex(50, edges=(f, 1), dtype=object) % 7
    i, j = np.nonzero(a.astype(object) != exact)
    assert (i + j).min() == 66
    assert 350 < len(i) < 450


# --- N1 arg_locs that reach outside the array --------------------------------------

def test_arg_locs_outside_the_array_read_zero():
    """N1. Phase 2: changed (C5, decision D5). (i-1, j-2) at column 1 is
    (i-1, -1), outside the array: it now reads 0. The notebook wrapped it
    around to the last column (a[1, 1] was 3).
    Migration: results change only for arg_locs that reach outside the
    array; none of the notebook's examples do."""
    a = ndplex(4, arg_locs=[[-1, 0], [0, -1], [-1, -2]],
               func=lambda x: x[0] + x[1] + x[2])
    assert a[1, 1] == 2            # 1 + 1 + 0
    # Zero padding computed independently: pad two zero columns on the left.
    n = 6
    ref = np.zeros((n + 1, n + 2), dtype=object)
    ref[1:, 2] = 1
    ref[1, 2:] = 1
    for i in range(1, n):
        for j in range(1, n):
            ref[i + 1, j + 2] = (ref[i, j + 2] + ref[i + 1, j + 1]
                                 + ref[i, j])
    got = ndplex(n, arg_locs=[[-1, 0], [0, -1], [-1, -2]],
                 func=lambda x: x[0] + x[1] + x[2])
    assert_array_equal(got.astype(object), ref[1:, 2:])


def test_arg_locs_none_still_means_on_the_edge():
    a = ndplex(5, arg_locs=[[-1, 0], [0, None]],
               func=lambda x: x[0] + x[1])
    # (i, j) = (i-1, j) + (i, 0): column 0 is the edge of ones
    assert_array_equal(a[:, 4], [1, 2, 3, 4, 5])


def test_default_3d_faces_do_not_depend_on_wrap():
    """The default 3-D arg_locs also index outside the array on the faces;
    they read 0, as in the notebook (where it held only by loop order)."""
    a = ndplex(6, edges=3)
    assert_array_equal(a[0], ndplex(6))


# --- N2 diag trims genuine zeros; all-zero input crashes -----------------------

def test_diag_keeps_genuine_trailing_zero():
    """N2. Phase 2: changed (C6, decision D6). The line ends where the move
    leaves the array, so the genuine zero at the end is kept (the notebook
    returned 7 values here).
    Migration: results change only where a diagonal ends in genuine zeros;
    none of the notebook's examples do."""
    osc = ndplex(8, func=lambda x: x[0] - x[1])
    assert_array_equal(osc[1], [1, 0, 1, 0, 1, 0, 1, 0])
    assert_array_equal(osc.diag(loc=(1, 0), move=(0, 1)), [1, 0, 1, 0, 1, 0, 1, 0])


def test_diag_of_all_zero_line():
    """N2. Phase 2: fixed (C6); the notebook raised IndexError."""
    c = np.arange(9)
    assert_array_equal(ndplex(9, edges=(c, -c)).diag(), np.zeros(9, dtype=int))


def test_as_tri_of_all_zero_array():
    """N2. Phase 2: fixed (C6); the notebook raised IndexError."""
    assert_array_equal(ndplex(4, edges=(0, 0)).as_tri(sums=True), [0, 0, 0, 0])


def test_as_tri_with_genuine_zeros_inside():
    c = np.arange(5)
    tri = ndplex(5, edges=(c, -c)).as_tri()
    assert tri.shape == (5, 5)
    assert_array_equal(tri[2], [2, 0, -2, 0, 0])


def test_diag_on_thin_slices():
    """Positions outside a side of length 1 read as 0 (they are not looked
    up in the array)."""
    p = ndplex(5)
    assert_array_equal(p[:1].diag(), [1])
    assert_array_equal(p[:, :1].diag(), [1])
    assert_array_equal(p[2:3].diag(move=(0, 1)), [1, 3, 6, 10, 15])


def test_diag_through_a_slice_with_a_side_of_one():
    """Squeezing a length-1 axis must not confuse where the line ends: the
    layers stepped through start at 1, so only three lie inside. (Found by
    the Phase 2 mutation check.)"""
    p = ndplex(4, edges=3)[:, :1, :]
    got = p.diag(loc=(1,), move=(1,))
    assert got.shape == (3, 4)
    assert_array_equal(got, np.asarray(p)[1:, 0, :])


def test_object_dtype_triangle_matches_int64():
    """The padding in as_tri is Python int 0 for dtype=object."""
    tri = ndplex(6, dtype=object).as_tri()
    assert tri.dtype == object
    assert_array_equal(tri.astype(np.int64), ndplex(6).as_tri())
    assert all(type(v) is int for v in tri.ravel())
    d = ndplex(6, dtype=object).diag(loc=(4, 0), move=(-1, 2))
    assert d.tolist() == [1, 10, 15] and all(type(v) is int for v in d)


def test_diag_that_starts_outside_the_array_is_empty():
    assert ndplex(4).diag(loc=(5, 5)).shape == (0,)


# --- N3 oeis hides network errors -------------------------------------------------

def test_oeis_reports_network_failure(capsys):
    """N3. Phase 2: changed (C8, decision D7). A failed lookup prints
    "lookup failed (...)"; the notebook printed "no match"."""
    oeis(np.array([1, 2, 3, 4, 5]))       # network is disabled in tests
    last = capsys.readouterr().out.splitlines()[-1]
    assert last.startswith("lookup failed (") and "network" in last


def test_oeis_quiet_raises_on_network_failure():
    with pytest.raises(OSError):
        oeis(np.array([1, 2, 3, 4, 5]), quiet=True)


# --- N4 argument handling -----------------------------------------------------------

def test_edges_accepts_numpy_int():
    """N4. Phase 2: fixed (C7)."""
    assert ndplex(3, edges=np.int64(3)).shape == (3, 3, 3)
    assert ndplex(3, edges=np.int32(2)).edges == (1, 1)


def test_edge_cases():
    """N4. Phase 2: changed (C7). Bad arguments raise ValueError with a
    message; the notebook raised IndexError for ndplex(0) and for positive
    arg_locs offsets (or, elsewhere, silently read uncomputed zeros).
    Migration: code catching IndexError for these must catch ValueError."""
    assert_array_equal(ndplex(1), [[1]])
    assert_array_equal(ndplex(4, edges=1), [1, 1, 1, 1])  # 1-D: just the edge
    def raises(exc, message):
        return pytest.raises(exc, match="^" + re.escape(message) + "$")

    with raises(ValueError, "nrows must be at least 1, got 0"):
        ndplex(0)
    with raises(ValueError, "edges must be at least 1, got 0"):
        ndplex(4, edges=0)
    with raises(ValueError, "edges must not be empty"):
        ndplex(4, edges=())
    with raises(ValueError, "edge 0 must be a number or a 1-D sequence of "
                            "length nrows=4; got shape (3,)"):
        ndplex(4, edges=([1, 2, 3], 1))  # edge of the wrong length
    with raises(ValueError, "edge 1 must be a number or a 1-D sequence of "
                            "length nrows=4; got shape (2, 2)"):
        ndplex(4, edges=(1, [[1, 2], [3, 4]]))
    with raises(ValueError, "arg_locs offsets must be <= 0 (or None), "
                            "got (0, 1)"):
        ndplex(5, arg_locs=[[-1, 0], [0, 1]])  # positive offset
    with raises(ValueError, "arg_locs offsets must be <= 0 (or None), "
                            "got (1, -1)"):
        ndplex(5, arg_locs=[[-1, 0], [1, -1]])  # positive, not past the edge
    with raises(ValueError, "each arg_loc needs 2 coordinates, got (-1, 0, 0)"):
        ndplex(5, arg_locs=[[-1, 0, 0]])
    with pytest.raises(TypeError):
        ndplex(5, arg_locs=[[-1.0, 0], [0, -1]])  # offsets must be integers
    with raises(ValueError, "as_tri needs an array of at least 2 dimensions"):
        ndplex(4, edges=1).as_tri()
    with raises(ValueError, "as_tri needs equal sides; the shape is (3, 4)"):
        ndplex(4)[1:].as_tri()
    with raises(ValueError, "each move needs 2 coordinates (as many as loc), "
                            "got (1, 1, 1)"):
        ndplex(4).diag(loc=(0, 0), move=(1, 1, 1))
    with raises(ValueError, "loc has 3 coordinates; the array has 2 dimensions"):
        ndplex(4).diag(loc=(0, 0, 0), move=(1, 1, 1))
    # numpy integers are fine everywhere an int is expected
    assert_array_equal(ndplex(np.int64(3), arg_locs=np.array([[-1, 0], [0, -1]])),
                       ndplex(3))


def test_default_dtype_is_int64():
    """N6. Phase 2: changed (C7). The default dtype is np.int64 everywhere;
    it was the platform int (int32 on Windows with NumPy 1.x)."""
    assert ndplex(3).dtype == np.int64
    assert ndplex(3, edges=3).dtype == np.int64


def test_current_diag_of_single_node_is_0d():
    """diag squeezes its result, so a 1-node ndplex gives a 0-d array, not
    shape (1,). (Found by the mutation check: removing np.squeeze survived.)
    Unchanged in Phase 2."""
    d = ndplex(1).diag()
    assert np.ndim(d) == 0 and d == 1
    assert np.ndim(ndplex(1, edges=3).diag()) == 0


def test_defaults():
    """F3, C5, C7. Phase 2: the defaults are arg_locs=None (was a mutable
    []) and func=sum (was lambda x: sum(x)); [] is still accepted.
    Migration: none."""
    d = ndplex.__new__.__defaults__
    assert d[1] is None and d[2] is sum
    assert_array_equal(ndplex(5, arg_locs=[]), ndplex(5))
