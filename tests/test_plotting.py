"""
Suite F -- plotting smoke tests (Agg backend; nothing is displayed).

These only check that each notebook-style call runs and draws something.
Pictures are not compared. diag_as_hist(normed=True) is broken on
matplotlib >= 3.9; that test is an expected failure until Phase 2 fixes it.
"""
import matplotlib
import matplotlib.pyplot as plt
import pytest

from _impl import diag_as_hist, ndplex, plot_ndplex

MPL = tuple(int(x) for x in matplotlib.__version__.split(".")[:2])

pytestmark = pytest.mark.filterwarnings(
    "ignore:FigureCanvasAgg is non-interactive:UserWarning")


@pytest.mark.parametrize("kwargs", [
    dict(move=(0, 1), loc=1, title="Pascal's Rectangle", caption="row 1"),
    dict(move=(1, 1), loc=0),
    dict(as_tri="center", title="Pascal's Triangle"),
    dict(move=(1, 1), loc=2, as_tri="center", invert_xaxis=True, xlabel=None),
    dict(move=(0, 1), as_tri="center", caption="Row sums"),
    dict(move=(-1, 1), as_tri=False, ylabel="row and diagonal"),
    dict(move=(-1, 1), as_tri="center", xlabel=None, ylabel=None),
    dict(as_tri="left"),
])
def test_plot_ndplex_runs(kwargs):
    plot_ndplex(ndplex(9), **kwargs)
    ax = plt.gcf().axes[0]
    assert len(ax.texts) == 45 if kwargs.get("as_tri") else len(ax.texts) == 81
    if kwargs.get("move") is not None:
        assert ax.lines


def test_diag_as_hist_unnormed_runs():
    y = ndplex(5, edges=2).diag(loc=(4, 0), move=(-1, 1))
    diag_as_hist(y, labels=["Base of Pascal's Triangle"], normed=False)
    ys = [ndplex(s).diag(loc=(s - 1, 0), move=(-1, 1)) for s in (8, 7, 6, 5)]
    diag_as_hist(ys, labels=[str(s) for s in (8, 7, 6, 5)], normed=False)


@pytest.mark.xfail(MPL >= (3, 9), raises=AttributeError, strict=True,
                   reason="Legend.legendHandles was removed in matplotlib 3.9 "
                          "(audit F7); fix in Phase 2")
def test_diag_as_hist_normed_runs():
    ys = [ndplex(s, dtype=float).diag(loc=(s - 1, 0), move=(-1, 1))
          for s in (5, 10, 20, 40)]
    diag_as_hist(ys, labels=["5", "10", "20", "40"], normed=True)

