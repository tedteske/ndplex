# Changelog

All notable changes to this project are documented here. The project follows [Semantic Versioning](https://semver.org/); while the version is 0.x, minor releases may change the API.

## 0.1.0 (2026-11-06)

First release, and the first version as a package. Before this, ndplex was the first code cell of `ndplex_array.ipynb` (Ted Teske, 2019–2024). The notebook's results are kept except where a change is listed below; each change is documented, with migration notes, in `docs/phase2_package.md`, `docs/phase3_ci.md` and `docs/phase4_release.md`.

- **Package layout.** `src/ndplex`: the `ndplex` class (`_core.py`) and `oeis` (`_oeis.py`). `from ndplex import ndplex, oeis` works as before. `import ndplex` needs only NumPy (≥ 1.23.5); `oeis` uses the standard library and is loaded on first use.
- **Plotting is left out.** `plot_ndplex` and `diag_as_hist` are not in the package; importing them raises an `ImportError` that points to the notebook in the repository, which has the original versions (Phase 4, C13; an examples notebook with working copies is planned).
- **No import side effects.** Importing no longer silences warnings or restyles matplotlib.
- **Overflow is reported.** If any node overflows the dtype, construction issues one `RuntimeWarning` naming the first node that did. Values are unchanged. `dtype=object` is exact, now including sums in `diag` and `as_tri` past 2^63.
- **Overflow is reported for every integer dtype, on every NumPy version** (Phase 3, `docs/phase3_ci.md`, C12). On NumPy < 2, overflow in int8, int16, int32 and unsigned arrays went unreported. An integer from `func` that does not fit the dtype is now wrapped and reported, where it used to wrap silently (NumPy < 2) or raise `OverflowError` (NumPy 2, or a Python int beyond int64).
- **CI.** Tests run on Linux (Python 3.10–3.15), macOS and Windows, on NumPy 1.23.5 and the latest NumPy.
- **Derived arrays keep working.** `diag` works on slices, arithmetic results, copies and unpickled arrays. Reductions (`sum`, `max`, ...) return plain scalars. Pickling keeps `edges`, `func` and `arg_locs` (a `func` that cannot be pickled comes back as `None`).
- **`arg_locs` outside the array read 0** instead of wrapping around to the far side. Positive offsets raise `ValueError`. The default is `arg_locs=None`.
- **`diag` ends where the moves leave the array**, so genuine trailing zeros are kept and all-zero lines return zeros instead of raising `IndexError`.
- **`as_tri` layers are left-justified in every dimension.** 2-D and 3-D are unchanged; from 4-D up the notebook's layers were sheared. Values and sums are unchanged.
- **Arguments.** NumPy integer `edges` accepted; bad arguments raise `ValueError` with a message; the default dtype is `np.int64` on every platform; the default `func` is the builtin `sum`.
- **`oeis`.** https and a timeout; network or format failures print `lookup failed (...)` instead of `no match`; `quiet=True` returns the results instead of printing.
- **Release.** Published to PyPI with Trusted Publishing (`.github/workflows/publish.yml`). The README is now the package's own documentation, and its examples run as tests. `CITATION.cff` added.
