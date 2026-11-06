# Changelog

All notable changes to this project are documented here. The project follows [Semantic Versioning](https://semver.org/); while the version is 0.x, minor releases may change the API.

## Unreleased (0.1.0.dev0)

First version as a package. Before this, ndplex was the first code cell of `ndplex_array.ipynb` (Ted Teske, 2019–2024). Everything the notebook computes is unchanged; the differences below are documented, with migration notes, in `docs/phase2_package.md`.

- **Package layout.** `src/ndplex`: the `ndplex` class (`_core.py`) and `oeis` (`_oeis.py`). `from ndplex import ndplex, oeis` works as before. `import ndplex` needs only NumPy (≥ 1.23.5); `oeis` uses the standard library and is loaded on first use.
- **Plotting is left out.** `plot_ndplex` and `diag_as_hist` are not in the package; importing them raises an `ImportError` that points to the examples notebook, which will carry a working copy.
- **No import side effects.** Importing no longer silences warnings or restyles matplotlib.
- **Overflow is reported.** If any node overflows the dtype, construction issues one `RuntimeWarning` naming the first node that did. Values are unchanged. `dtype=object` is exact, now including sums in `diag` and `as_tri` past 2^63.
- **Derived arrays keep working.** `diag` works on slices, arithmetic results, copies and unpickled arrays. Reductions (`sum`, `max`, ...) return plain scalars. Pickling keeps `edges`, `func` and `arg_locs` (a `func` that cannot be pickled comes back as `None`).
- **`arg_locs` outside the array read 0** instead of wrapping around to the far side. Positive offsets raise `ValueError`. The default is `arg_locs=None`.
- **`diag` ends where the moves leave the array**, so genuine trailing zeros are kept and all-zero lines return zeros instead of raising `IndexError`.
- **Arguments.** NumPy integer `edges` accepted; bad arguments raise `ValueError` with a message; the default dtype is `np.int64` on every platform; the default `func` is the builtin `sum`.
- **`oeis`.** https and a timeout; network or format failures print `lookup failed (...)` instead of `no match`; `quiet=True` returns the results instead of printing.
