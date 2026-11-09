"""
ndplex -- the n-Dimensional m-Plex array: a generic Pascal's array (rectangle,
cube or higher) with user-defined edges and node-generating function.

    from ndplex import ndplex, oeis

    p = ndplex(9)              # Pascal's rectangle, 9 x 9
    p.diag(loc=(4, 0), move=(-1, 1))   # row 4 of Pascal's triangle
    p.as_tri()                 # the whole triangle, justified left
    oeis(p.as_tri(), trim=True, size=5)   # look the rows up on oeis.org

`import ndplex` needs only numpy. `oeis` is loaded on first use and needs
network access when called.

Attribution (see ATTRIBUTION.md for the tiered breakdown and references):
  - Original work (2019-2024): Ted Teske -- the ndplex array, diag, as_tri
    and oeis, in the notebook ndplex_array.ipynb.
  - Packaging and the Phase 2 fixes (2026): Ted Teske with Claude (Anthropic).
"""
from ._core import ndplex

__version__ = "0.1.0"

__all__ = ["ndplex", "oeis", "__version__"]

_MOVED = (
    "is not part of the ndplex package (from 0.1.0, plotting is left to the "
    "user). A working copy is in the helper cell of the examples notebook, "
    "notebooks/ndplex_examples.ipynb: "
    "https://github.com/tedteske/ndplex/blob/master/notebooks/ndplex_examples.ipynb")


def __getattr__(name):
    if name == "oeis":
        from ._oeis import oeis
        return oeis
    if name in ("plot_ndplex", "diag_as_hist"):
        raise ImportError(f"{name} {_MOVED}")
    raise AttributeError(f"module 'ndplex' has no attribute {name!r}")


def __dir__():
    return sorted(set(globals()) | {"oeis"})
