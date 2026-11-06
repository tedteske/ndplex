"""
Suite G -- known issues found by the Phase 1 audit (docs/phase1_audit.md).

Two kinds of test, each tied to a finding number in the audit note:

* `xfail(strict=True)` tests state the behaviour we expect a package to
  have, where the fix is not in doubt. They fail today. When Phase 2 fixes
  the bug they XPASS, which strict mode reports as a failure, so the marker
  must be removed in the same change.
* `test_current_*` tests pin today's behaviour where what to do is Ted's
  decision (Phase 2). If a decision changes the behaviour, the test is
  rewritten with a migration note, not silently deleted.
"""
import math
import pickle
import subprocess
import sys
import warnings

import numpy as np
import pytest
from numpy.testing import assert_array_equal

from _impl import PATH, impl, ndplex, oeis

STRICT = dict(strict=True)


# --- F1 import-time side effects ----------------------------------------------

def _import_in_fresh_process(code):
    prog = (
        "import sys, importlib.util, matplotlib; matplotlib.use('Agg')\n"
        "import warnings, matplotlib as mpl\n"
        f"spec = importlib.util.spec_from_file_location('m', {str(PATH)!r})\n"
        "m = importlib.util.module_from_spec(spec)\n"
        "before = (list(warnings.filters), dict(mpl.rcParams))\n"
        "spec.loader.exec_module(m)\n" + code)
    return subprocess.run([sys.executable, "-c", prog], capture_output=True,
                          text=True, check=True).stdout.strip()


@pytest.mark.xfail(reason="F1: import calls warnings.simplefilter('ignore')", **STRICT)
def test_import_leaves_warning_filters_alone():
    out = _import_in_fresh_process("print(list(warnings.filters) == before[0])")
    assert out == "True"


@pytest.mark.xfail(reason="F1: import calls sns.set(style='darkgrid')", **STRICT)
def test_import_leaves_matplotlib_style_alone():
    out = _import_in_fresh_process(
        "print(mpl.rcParams['axes.facecolor'] == before[1]['axes.facecolor'])")
    assert out == "True"


@pytest.mark.xfail(reason="F1: plot_ndplex sets rcParams['font.family']", **STRICT)
def test_plot_ndplex_leaves_global_font_alone():
    import matplotlib as mpl
    before = list(mpl.rcParams["font.family"])
    try:
        impl.plot_ndplex(ndplex(3))
        assert list(mpl.rcParams["font.family"]) == before
    finally:
        mpl.rcParams["font.family"] = before


@pytest.mark.xfail(reason="F2: import pulls in scipy, seaborn, requests", **STRICT)
def test_import_needs_only_numpy():
    out = _import_in_fresh_process(
        "print(sorted(k for k in ('scipy', 'seaborn', 'requests', "
        "'matplotlib.pyplot') if k in sys.modules))")
    assert out == "[]"


# --- F4 ndarray subclass ---------------------------------------------------------

@pytest.mark.xfail(raises=AttributeError, reason="F4: slices lose nrows", **STRICT)
def test_diag_works_on_a_slice():
    assert_array_equal(ndplex(5)[1:].diag(), [1, 3, 10, 35])


@pytest.mark.xfail(raises=AttributeError, reason="F4: arithmetic loses nrows", **STRICT)
def test_diag_works_after_arithmetic():
    assert_array_equal((ndplex(4) * 2).diag(), [2, 4, 12, 40])


@pytest.mark.xfail(raises=AttributeError, reason="F4: pickle loses attributes", **STRICT)
def test_pickle_round_trip_keeps_methods_working():
    q = pickle.loads(pickle.dumps(ndplex(4)))
    assert_array_equal(q.diag(), [1, 2, 6, 20])


def test_current_result_types():
    p = ndplex(4)
    assert type(p[1]) is type(p)            # slices stay ndplex ...
    assert type(p + 1) is type(p)           # ... arithmetic too ...
    assert not hasattr(p[1:], "nrows")      # ... but without attributes
    assert type(p.sum()) is type(p)         # a 0-d ndplex, not a scalar
    assert type(ndplex(4, dtype=float).round(1)) is np.ndarray
    assert type(p.diag()) is np.ndarray
    assert type(p.as_tri()) is np.ndarray


# --- F5 integer overflow ---------------------------------------------------------

@pytest.mark.filterwarnings("ignore:overflow encountered:RuntimeWarning")
def test_current_int64_overflow_wraps_silently_after_66():
    n = 70
    got = ndplex(n).astype(object)
    exact = np.array([[math.comb(i + j, i) for j in range(n)] for i in range(n)],
                     dtype=object)
    wrong = got != exact
    i, j = np.nonzero(wrong)
    assert (i + j).min() == 67  # every node with i + j <= 66 is exact
    # wrapping is modulo 2**64, so residues mod powers of 2 survive ...
    assert ((got % 8) == (exact % 8)).all()
    # ... and others do not (the notebook's "divisor 5" heatmap)
    assert not ((got % 5) == (exact % 5)).all()


def test_overflow_warns_when_warnings_are_not_silenced():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        ndplex(70)
    assert any("overflow" in str(x.message) for x in w)


def test_object_dtype_is_exact():
    """dtype=object stores Python ints, so construction and diag are exact."""
    n = 100
    got = ndplex(n, dtype=object)
    assert got[n - 1, n - 1] == math.comb(2 * n - 2, n - 1)
    assert got.diag()[-1] == math.comb(2 * n - 2, n - 1)
    assert ndplex(60, dtype=object).as_tri(sums=True)[-1] == 2 ** 59


@pytest.mark.xfail(raises=OverflowError, **STRICT,
                   reason="N12: diag/as_tri pad object arrays with np.int64 "
                          "zeros, so sums past 2**63 overflow")
def test_object_dtype_sums_past_int64():
    assert ndplex(100, dtype=object).as_tri(sums=True)[-1] == 2 ** 99


@pytest.mark.filterwarnings("ignore:overflow encountered:RuntimeWarning")
def test_current_fibonacci_mod_7_heatmap_is_partly_overflowed():
    """Notebook cell 226 heatmaps ndplex(50, edges=(fib, 1)) % 7. Its lower
    right part (i + j >= 66) is overflow, not pattern."""
    f = [1, 1]
    for _ in range(48):
        f.append(f[-1] + f[-2])
    a = ndplex(50, edges=(f, 1)) % 7
    exact = ndplex(50, edges=(f, 1), dtype=object) % 7
    i, j = np.nonzero(a.astype(object) != exact)
    assert (i + j).min() == 66
    assert 350 < len(i) < 450


# --- N1 arg_locs that reach outside the array wrap around ----------------------

def test_current_arg_locs_wrap_around():
    """(i-1, j-2) at column 1 is (i-1, -1): numpy wraps it to the last
    column instead of treating it as outside the array."""
    a = ndplex(4, arg_locs=[[-1, 0], [0, -1], [-1, -2]],
               func=lambda x: x[0] + x[1] + x[2])
    assert a[1, 1] == 3            # 1 + 1 + a[0, -1] (=1, wrapped)
    # zero padding would give 1 + 1 + 0 = 2


def test_default_3d_faces_do_not_depend_on_wrap():
    """The default 3-D arg_locs also index outside the array on the faces,
    but the wrapped node has not been computed yet, so it reads 0."""
    a = ndplex(6, edges=3)
    assert_array_equal(a[0], ndplex(6))


# --- N2 diag trims genuine zeros; all-zero input crashes -----------------------

def test_current_diag_drops_genuine_trailing_zero():
    osc = ndplex(8, func=lambda x: x[0] - x[1])
    assert_array_equal(osc[1], [1, 0, 1, 0, 1, 0, 1, 0])
    assert_array_equal(osc.diag(loc=(1, 0), move=(0, 1)), [1, 0, 1, 0, 1, 0, 1])


@pytest.mark.xfail(raises=IndexError, reason="N2: all-zero diagonal", **STRICT)
def test_diag_of_all_zero_line():
    c = np.arange(9)
    assert_array_equal(ndplex(9, edges=(c, -c)).diag(), np.zeros(9, dtype=int))


@pytest.mark.xfail(raises=IndexError, reason="N2: all-zero array", **STRICT)
def test_as_tri_of_all_zero_array():
    assert_array_equal(ndplex(4, edges=(0, 0)).as_tri(sums=True), [0, 0, 0, 0])


# --- N3 oeis hides network errors -------------------------------------------------

def test_current_oeis_reports_network_failure_as_no_match(capsys):
    oeis(np.array([1, 2, 3, 4, 5]))       # network is disabled in tests
    assert capsys.readouterr().out.splitlines()[-1] == "no match"


# --- N4 argument handling -----------------------------------------------------------

@pytest.mark.xfail(raises=TypeError, reason="N4: numpy int edges", **STRICT)
def test_edges_accepts_numpy_int():
    assert ndplex(3, edges=np.int64(3)).shape == (3, 3, 3)


def test_current_edge_cases():
    assert_array_equal(ndplex(1), [[1]])
    assert_array_equal(ndplex(4, edges=1), [1, 1, 1, 1])  # 1-D: just the edge
    with pytest.raises(IndexError):
        ndplex(0)
    with pytest.raises(ValueError):
        ndplex(4, edges=([1, 2, 3], 1))  # edge of the wrong length
    with pytest.raises(IndexError):
        ndplex(5, arg_locs=[[-1, 0], [0, 1]])  # positive offset


def test_default_arg_locs_list_is_not_mutated():
    """F3: the mutable default is reassigned, never mutated, so it is
    harmless as written."""
    ndplex(3)
    ndplex(3, edges=3)
    assert ndplex.__new__.__defaults__[1] == []
