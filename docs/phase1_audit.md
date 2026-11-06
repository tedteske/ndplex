# ndplex — Phase 1: Audit

**Status:** audit complete; nothing in the library has been changed. This phase adds a regression suite (`tests/`, 126 passing tests and 12 expected failures), a mutation check for it, `ATTRIBUTION.md`, and this note. Section 7 proposes the 0.1.0 API; section 8 lists the decisions needed before Phase 2.

**Source audited:** `ndplex_array.ipynb` at commit `7560854` (2024-04-13). The library is the notebook's first code cell (517 lines), copied verbatim to `tests/ndplex_original.py`. The notebook has 279 cells: 143 code cells (the library plus 142 examples) and 136 markdown cells.

**Environment:** Python 3.12.3 (Colab's version family), numpy 2.5.4, scipy 1.18.1, matplotlib 3.11.2, seaborn 0.13.2, pandas 3.1.1, requests 2.34.2, pytest 9.2.0, all current on PyPI on 6 Nov 2026. This sandbox could not reach oeis.org or gist.githubusercontent.com.

**Epistemic labels.** *Run* = observed by running the code here; true for what was run, not a guarantee beyond it. *Numerical* = checked over a stated range, not proved. *Proved* = a short argument given in the text. *Not checked* = could not be run here.

---

## 1. Summary

- The mathematics holds up. Every numeric result the notebook prints is reproduced exactly by today's libraries (*Run*), and the suite pins them. Property checks extend them: default nodes are binomial and multinomial coefficients, and layer sums are powers of 2, 3 and 4 (*Numerical*, sizes in each test; the multinomial theorem makes the sums *Proved*).
- One plotting function is broken. `diag_as_hist(..., normed=True)` raises `AttributeError` on matplotlib 3.9 and later, so 10 notebook cells fail in a fresh Colab-like environment (F7).
- Integer overflow is real, silent, and hidden by the library itself. The library's import silences all warnings, including numpy's overflow warning. The default 2-D array is wrong from i + j = 67 on (F5). One of the notebook's puzzles (the Fibonacci heatmap mod 7) is partly drawn from overflowed values.
- New issues not in the context file: `arg_locs` offsets that reach outside the array wrap around to the far side (N1); `diag` drops genuine trailing zeros and crashes on all-zero lines (N2); `oeis` reports network errors as "no match" (N3); `plot_ndplex` changes the global font (F1); `dtype=object` is exact except for sums in `diag`/`as_tri` past 2^63 (N12).
- Speed is fine for everything the notebook does (whole notebook: 12 s). No optimization is needed for 0.1.0 (F6).

---

## 2. The notebook, run top to bottom

Two fresh-kernel runs with `nbclient`, outputs compared with the saved ones. Text outputs are compared exactly; figures are compared only by count (every cell drew the same number as before). Cell numbers are 0-based positions in the notebook, markdown cells included, as in `tests/` docstrings.

**Run A, as written** (*Run*):

- **Errors from matplotlib (10 cells).** Cells 160, 185, 188, 190, 192, 194, 195, 197, 221 and 230: `AttributeError: 'Legend' object has no attribute 'legendHandles'`, raised by `diag_as_hist(..., normed=True)`. Cell 230 therefore also never prints its "Average rental rate = $475.96". Cells calling it with `normed=False` (108, 109, 187, 199) still work. See F7.
- **The primes download (1 cell, then 28 more).** Cell 233 downloads the first 1000 primes from a GitHub gist and fails offline. Every later cell that uses `primes`, `primesfrom2to` or their results then fails (cells 236–277, mostly `NameError`; cell 238 raises `ValueError` because `p` is left over from an earlier cell). *Not checked:* the gist was unreachable here. Run B shows that with the primes supplied, all 28 cells reproduce their saved outputs, apart from the two OEIS lookups among them.
- **OEIS lookups (8 cells).** Cells 16, 70, 80, 100, 219, 224, 241 and 262 printed "no match" for every row, because the network was blocked and `oeis()` reports any exception as "no match" (N3). *Not checked:* whether today's oeis.org still returns the `%N` text format the parser relies on. Ted can check in Colab: `oeis(ndplex(5))` should print five A-numbers.
- **NumPy 2 printing (5 cells, values unchanged).** NumPy 2 changed how scalars print. Cells 24 and 30 print `[np.int64(1), np.int64(2), ...]` instead of `[1, 2, ...]`; cells 208, 212 and 214 print `np.float64(1.618033988749895)`, `np.int64(1278)` and `np.int64(1149)`. The examples can use `.tolist()` or `int()`.
- Every other cell matches its saved output exactly.

**Run B, warnings re-enabled and the primes supplied offline** (*Run*). The library's `warnings.simplefilter('ignore')` was undone right after the library cell, and the gist download was answered with the first 1000 primes from a sieve.

- **Integer overflow warnings (6 cells).** `RuntimeWarning: overflow encountered in scalar add` in cell 132 (Sierpinski, divisor 2), 134 (divisor 4), 136 (divisor 5), 208 (golden ratio, `ndplex(50)`), 212 (Narayana's cows, `ndplex(50)`) and 226 (Fibonacci edges, mod 7). See F5 for which of these results are affected.
- **Divide by zero (2 cells).** Cells 121 and 123: the first ratio is `inf` because the diagonal starts with 0. Expected; the saved output shows `inf` too.
- **No deprecation warnings.** No `DeprecationWarning` or `FutureWarning` from numpy, matplotlib, seaborn or pandas in any cell.
- **Primes section.** With the primes supplied, cells 236–277 match their saved outputs (except the OEIS cells 241 and 262), including the `np.float128` heatmap (cell 264) on Linux.
- **Time.** Whole notebook 12.0 s; slowest cell is the library cell itself (1.1 s, mostly imports); no example cell over 0.6 s.

---

## 3. The context file's issues, confirmed or corrected

**F1. Import-time side effects — confirmed, and one more** (*Run*).

- Importing the cell puts `('ignore', Warning)` first in `warnings.filters`, silencing every warning in the session, including numpy's overflow warnings (F5).
- `sns.set(style="darkgrid")` restyles all matplotlib plots (e.g. `axes.facecolor` white → `#EAEAF2`).
- New: `plot_ndplex` sets `plt.rcParams["font.family"] = "serif"`, which changes the font of every later plot in the session.
- Tests: `test_import_leaves_warning_filters_alone`, `test_import_leaves_matplotlib_style_alone`, `test_plot_ndplex_leaves_global_font_alone` (expected failures).

**F2. Heavy dependencies — confirmed, and smaller than thought** (*Run*).

- Import loads numpy, scipy.stats, matplotlib.pyplot, seaborn (and through it pandas) and requests: about 1.1 s, against 0.05 s for numpy alone.
- The library itself uses seaborn only for the `sns.set` call, scipy only for `norm.pdf` in `diag_as_hist`, and requests only in `oeis`. The class needs only numpy. The notebook's examples use seaborn and pandas directly (`heatmap`, `lineplot`, `DataFrame`); those stay notebook imports.
- So the core can be numpy-only, plotting needs only matplotlib (the normal pdf is one line of numpy), and `oeis` can use the standard library's `urllib` instead of requests.

**F3. Mutable and lambda defaults — confirmed but harmless as written** (*Run*).

- `arg_locs=[]` is reassigned, never mutated, so no state leaks between calls (`test_default_arg_locs_list_is_not_mutated`).
- `func=lambda x: sum(x)` is equivalent to the builtin `sum` (`test_equivalent_default_funcs`). A lambda default only matters if `func` is ever pickled (F4).

**F4. ndarray subclass — confirmed, worse than listed** (*Run*).

- Slices, arithmetic, `copy()`, `view()`, `deepcopy` and pickling all return an `ndplex` with no `nrows`, `edges`, `func` or `arg_locs`, because there is no `__array_finalize__`. Calling `.diag()` or `.as_tri()` on any of them raises `AttributeError` (e.g. `ndplex(5)[1:].diag()`, `(ndplex(4) * 2).diag()`, a pickled-and-loaded array).
- Results are inconsistent in type: `p[1]`, `p + 1`, `p == p` and `p.T` are `ndplex`; `p.sum()` and `np.max(p)` are 0-d `ndplex` arrays (they print as `ndplex(12870)`); `p.round(3)` is a plain `ndarray`; `diag` and `as_tri` return plain `ndarray`.
- Tests: `test_diag_works_on_a_slice`, `test_diag_works_after_arithmetic`, `test_pickle_round_trip_keeps_methods_working` (expected failures); `test_current_result_types` pins the rest.

**F5. Integer overflow — confirmed, located, and partly explained.**

- *Where it starts* (*Run*). Default 2-D int64: every node with i + j ≤ 66 is exact; the first wrong node is at i + j = 67 (C(67, 30) > 2^63). Of a 100 × 100 array, 6036 of 10 000 nodes are wrong. 3-D int64 is wrong from i + j + k = 44. With int32 (numpy's default `int` on Windows before NumPy 2), from i + j = 34.
- *It is silent.* numpy warns on each overflowing scalar add, but F1's filter hides it (`test_overflow_warns_when_warnings_are_not_silenced`).
- *Why powers of 2 survive* (*Proved*, and *Run* for 2, 4, 8 on 100 × 100). int64 addition is addition modulo 2^64, and reduction modulo 2^k (k ≤ 64) respects addition, so overflowed values still have the right residues modulo 2, 4, 8, … but not modulo 3, 5 or 7. This answers the notebook's "Curiously, you do not need to make this correction if divisor is a power of 2". The Sierpinski heatmaps (cells 132, 134) are therefore correct; the divisor-5 heatmap (cell 136) is not, as the notebook says.
- *The Fibonacci puzzle* (cell 226, `ndplex(50, edges=(fibonaccis(50), 1)) % 7`): 405 of its 2500 cells are overflow, all with i + j ≥ 66 (the lower-right corner of the picture). The diagonal stripes are genuine: they appear, more cleanly, when the array is built with `dtype=object` (*Run*, `test_current_fibonacci_mod_7_heatmap_is_partly_overflowed`).
- *Unaffected examples* (*Run*): the golden ratio and Narayana's cows cells build `ndplex(50)`, which overflows in its far corner, but the diagonals they sum stay small, so all 50 Fibonacci and Narayana numbers are exact.
- *What already works:* `dtype=object` stores Python integers and is exact for any size, at about the same speed (0.15 s vs 0.12 s for 100 × 100), because the node loop is Python either way. `dtype=float` is accurate to 6e-16 relative error up to 100 × 100. But see N12: with `dtype=object`, sums taken by `diag` or `as_tri` raise `OverflowError` once they pass 2^63.
- Suggested handling: decision D3.

**F6. Speed — measured; no action needed for 0.1.0** (*Run*).

- 60 000–120 000 nodes per second: `ndplex(100)` 0.12 s, `ndplex(200)` 0.34 s, `ndplex(40, edges=3)` 0.87 s, `ndplex(15, edges=4)` 0.90 s. `diag` and `as_tri` are vectorized and fast (`as_tri` on 200 × 200: 0.07 s).
- The largest notebook array takes under 0.6 s. A million-node array would take about 10–15 s. The default Pascal rule has a closed form and could be vectorized later if anyone needs large arrays.

**F7. Plotting deprecations — corrected.**

- The context file expected seaborn deprecations. There are none: no seaborn call in the notebook warns with seaborn 0.13.2, and `distplot` appears only in a docstring comment (*Run*).
- The real break is matplotlib: `diag_as_hist` uses `Legend.legendHandles`, renamed `legend_handles` in 3.7 and removed in 3.9 (*Run*: present on matplotlib 3.6.3, both names on 3.7.5, only `legend_handles` on 3.9.0). It fails every `normed=True` call (10 notebook cells). The fix is a one-word rename (`test_diag_as_hist_normed_runs`, an expected failure on matplotlib ≥ 3.9).
- `plot_ndplex` and `diag_as_hist` call `plt.show()` and return `None`, so their figures cannot be adjusted or saved afterwards. `diag_as_hist` has six colours and raises `IndexError` for a seventh data set.

**F8. External data — confirmed; one more portability issue.**

- The primes download is one cell, but 28 later cells depend on it (section 2). The tests use an offline sieve (`tests/primes.py`) and no test touches the network: `tests/conftest.py` disables sockets for every test.
- Cell 264 uses `np.float128`, which exists on Linux x86 (Colab) but not on Windows or Apple-silicon Macs. It only holds 0s and 1s, so any dtype works.

**F9. No tests — resolved by this phase** (section 5).

**Small corrections to the context file.** The notebook has 279 cells (143 code), not about 275 examples. `as_tri` returns its result; its docstring says "Prints".

---

## 4. New findings

**N1. `arg_locs` that reach outside the array wrap around** (*Run*).

- A relative location is added to the node's index, and numpy reads a negative index from the far end. With `arg_locs=[[-1, 0], [0, -1], [-1, -2]]`, node (1, 1) reads node (0, −1) = (0, n − 1) = 1, giving 3 where zero padding would give 2. 25 of 36 nodes of a 6 × 6 array differ (`test_current_arg_locs_wrap_around`).
- The default `arg_locs` also index outside the array, on the faces of 3-D and higher arrays (e.g. node (0, i, j) reads (−1, i, j)), but the wrapped node is always one that has not been computed yet, so it reads 0 and the result equals zero padding (*Run*, 6 × 6 × 6; `test_default_3d_faces_do_not_depend_on_wrap`). This depends on the loop order.
- Positive offsets (documented as not allowed) raise `IndexError` when they reach past the far edge (*Run*); elsewhere they read nodes not yet computed, which are still 0 (from reading the loop).
- None of the notebook's examples reach outside the array.

**N2. `diag` cannot tell padding from data** (*Run*).

- `diag` pads with zeros, follows the moves, then trims trailing all-zero rows. Genuine zeros at the end are trimmed too: row 1 of `ndplex(8, func=lambda x: x[0] - x[1])` is `[1, 0, 1, 0, 1, 0, 1, 0]`, but `diag(loc=(1, 0), move=(0, 1))` returns seven values.
- A line or array that is all zeros makes the trimming loop run off the end: `IndexError` (e.g. the main diagonal of the notebook's `ndplex(9, edges=(c, -c))`, or `ndplex(4, edges=(0, 0)).as_tri()`).
- `as_tri` also uses zeros as padding, so a genuine zero inside a triangle looks like padding. That is inherent in returning a rectangular array; it only needs documenting.

**N3. `oeis` hides failures** (*Run*, stubbed).

- A bare `except:` turns every error, including no network, a timeout or a changed response format, into "no match".
- It uses `http://` rather than `https://`, and no timeout.
- It prints and returns `None`, so results cannot be used in code.
- *Not checked:* the live response format.

**N4. Argument handling** (*Run*).

- `edges=np.int64(3)` raises `TypeError` (the check is `type(edges) is int`).
- `ndplex(0)` raises `IndexError`; an edge of the wrong length raises numpy's broadcast `ValueError`.
- `edges=1` gives a 1-D array that is just the edge; `as_tri` on it raises `IndexError`.

**N5. `plot_ndplex` details** (*Run*). It draws only nodes greater than 0, so zeros and negative values are blank (the `edges=(c, -c)` example would plot only its lower triangle). Its first parameter is named `ndplex`, shadowing the class inside the function. It handles 2-D arrays only.

**N6. Default dtype.** `dtype=int` is int64 on Linux, macOS and NumPy 2 everywhere, but int32 on Windows with NumPy 1.x, where overflow starts at i + j = 34.

**N7. Third-party code in the library** (see ATTRIBUTION.md). `trim_trailing_zeros` is adapted from a Stack Overflow answer (CC BY-SA, share-alike); the `oeis` query is adapted from Andrew Walker's `oeis` (BSD per its setup.py). Both are small and would be rewritten anyway by the fixes for N2 and N3 (decision D9).

**N8. One example's edge effect.** The last example (cell 276) finds each node's distance to the nearest prime using primes below the array's maximum, so the maximum node (223 653) reports 16 instead of 14. Only that cell is affected; it is an example, not the library.

**N12. `dtype=object` sums** (*Run*). `diag` and `as_tri` pad with `np.pad`, which inserts numpy int64 zeros into an object array. Adding a Python integer above 2^63 to one raises `OverflowError`, so `ndplex(100, dtype=object).as_tri(sums=True)` fails although the array itself is exact (`test_object_dtype_sums_past_int64`, an expected failure).

---

## 5. The regression suite

Run with `pip install numpy scipy matplotlib seaborn requests pytest` and then `pytest tests`. In Phase 1 the tests run against `tests/ndplex_original.py`; `tests/_impl.py` is the one place to change when they move to the package in Phase 2.

Result: **126 passed, 12 expected failures (xfail), in about 8 s** (*Run*). No test uses the network.

- **Suite A, `test_pascal_2d.py`** (32 tests): the 9 × 9 rectangle, rows, columns, diagonals, the triangle by `diag` and by `as_tri`, `as_tri(start, end)`, row sums as powers of 2; nodes equal C(i + j, i) for sizes 1–30.
- **Suite B, `test_3d_4d.py`** (17): the 5 × 5 × 5 tetrahedron array, oblong numbers, the main diagonal, cross-sections, `as_tri` layers as trinomial triangles, layer sums as powers of 3 and 4, 4-D nodes as multinomials, `func=lambda x: 1` giving triangular, tetrahedral and 4-simplex numbers, the 3-D prime-edge diagonal.
- **Suite C, `test_edges_func_arglocs.py`** (28): edge orientation (`edges[0]` fills column 0, `edges[-1]` fills row 0, and the last edge wins at the origin; the docstring does not say this), every `edges`, `func` and `arg_locs` example, simplex/duplex/triplex triangles and their sums, the golden ratio from a ratio rule, and the heatmap claims: Sierpinski mod 2 equals Lucas's theorem, the modulus inside `func` is exact, digit sums are digital roots.
- **Suite D, `test_sequences.py`** (18): Fibonacci and Narayana's cows from steep diagonals (to 50 terms), cows at year 20 with and without mortality (1278, 1149), the slope table, the adjacent-ratio examples, the average rental rate ($475.96), and all the primes examples.
- **Suite E, `test_oeis.py`** (9): with a fake `requests.get`, the request (`http://oeis.org/search`, `q=1,2,3`, `n=1`, `fmt=text`), parsing of the `%N` line, 1-D and 2-D input, `size`, `trim`, and no match.
- **Suite F, `test_plotting.py`** (10): `plot_ndplex` with each notebook-style call draws the right number of nodes and the highlight lines; `diag_as_hist` with `normed=False`; `normed=True` as an expected failure (F7). Pictures are not compared.
- **Suite G, `test_known_issues.py`** (23): one test per finding above. Expected failures state the intended fix where it is not in doubt; `test_current_*` tests pin today's behaviour where the fix is a decision.
- **`test_original_copy.py`** (1): `tests/ndplex_original.py` is byte-for-byte the notebook cell.

How the expected failures work: each is marked `xfail(strict=True)`. When Phase 2 fixes the bug the test passes, strict mode reports that as a failure, and the marker must come off in the same commit. So no fix lands unrecorded, and no recorded issue is forgotten.

---

## 6. Mutation check

`tests/mutation_check.py` makes one small change at a time to the class and to `oeis` in `tests/ndplex_original.py`, runs the whole suite against the changed copy, and records whether any test fails. Operators: arithmetic and comparison swaps, integer constants ±1, removed unary minus, `and`/`or` swaps, negated `if`/`while` conditions, changed strings, flipped booleans, and every statement in turn replaced by `pass`. Plotting functions were not mutated (they are only smoke-tested).

Result (*Run*, 6 Nov 2026): **281 mutants; 269 killed, 3 killed by timeout (an endless loop in `diag`'s zero-trimming), 9 survived.**

- **One gap, now closed.** Deleting `np.squeeze` in `diag` survived; it only matters for a 1 × 1 array, where `diag` returns a 0-d array. `test_current_diag_of_single_node_is_0d` now pins this, and the mutant is killed (re-run).
- **Eight equivalent mutants** (same behaviour on every valid input; argued from the code, not proved by exhaustive test):
    - Deleting `edge_loc.append(slice(None))`: indexing with one fewer index already selects the whole last axis.
    - `e[0] * -1` → `e[0] / -1` in `as_tri`: the float result is stored back into an integer array, giving the same values.
    - `move[0]` → `move[-1]` in the scalar check: a single move has all-scalar entries, a list of moves all-tuple entries.
    - `fancy_index >= pad_row` → `>`, and `fancy_index < 0` → `< -1`: index `nrows` and index −1 both land on the zero pad row anyway.
    - Padding `(0, 1)` → `(0, 2)`: more zero padding, same reads.
    - `min(-1, last_row + 1)` → `min(1, ...)` or `min(0, ...)`: the loop always leaves `last_row + 1 ≤ -1`, so the `min` never binds.
- `oeis`: all 53 mutants killed.

The harness is reusable: in Phase 2, pointing it at the package (`--src`) checks that the suite still guards the rewritten code.

---

## 7. Proposed 0.1.0 API

Nothing below has been implemented. Each change from the notebook carries a migration note.

**Package layout** (as in bounded-lognorm):

- `src/ndplex/__init__.py`: exports `ndplex` and `__version__`. `oeis`, `plot_ndplex` and `diag_as_hist` are importable from the top level too, but loaded only when first used (a module `__getattr__`), so `import ndplex` needs only numpy.
- `src/ndplex/_core.py`: the class. numpy only.
- `src/ndplex/plot.py`: `plot_ndplex`, `diag_as_hist`. Needs matplotlib (`pip install ndplex[plot]`).
- `src/ndplex/oeis.py`: `oeis`. Standard library only.
- Dependencies: `numpy>=1.23.5`; extra `plot = ["matplotlib>=3.7"]` (3.7 is the first with `legend_handles`). scipy, seaborn, requests and pandas are dropped from the library. The notebook keeps its own seaborn and pandas imports (both are in Colab).

**What stays as it is:**

- The name and call: `ndplex(nrows, edges=(1, 1), arg_locs=..., func=..., dtype=...)`, with `edges` as an int (number of edges of ones) or a sequence of numbers or 1-D arrays, and `None` in `arg_locs` meaning "on the edge".
- Every value the notebook computes (Suites A–D pin them).
- `diag(loc, move, sum_axis)` and `as_tri(start, end, sums)`, their arguments and their results on every notebook example.
- `oeis`, `plot_ndplex` and `diag_as_hist` names, arguments and printed or drawn output.

**What changes** (each with its migration note):

- **C1. No import side effects** (F1). Import no longer silences warnings or restyles plots; `plot_ndplex` sets the serif font on its own text only. *Migration:* for the old look, add `import seaborn as sns; sns.set_theme(style="darkgrid")` to the notebook. Warnings (notably overflow) now appear.
- **C2. Lighter imports** (F2). `import ndplex` loads only numpy. *Migration:* `from ndplex import ndplex, oeis, plot_ndplex, diag_as_hist` keeps working; plotting needs `pip install ndplex[plot]` outside Colab.
- **C3. Overflow is reported** (F5, D3). Proposed: if any node overflows int64, construction issues one `RuntimeWarning` naming the first node that overflowed and suggesting `dtype=object`; values are unchanged. `dtype=object` becomes the documented exact route, with N12 fixed so its sums are exact too. *Migration:* none for results; examples that overflow on purpose (Sierpinski mod 2 and 4) can silence the warning or use `dtype=object`.
- **C4. Arrays derived from an ndplex keep working** (F4, D4). Proposed: `nrows` is read from the shape; `edges`, `func` and `arg_locs` are carried through views and copies; `diag`/`as_tri` on a non-cubic slice raise a clear `ValueError`; reductions (`sum`, `max`, ...) return plain scalars; pickling keeps the metadata. *Migration:* `np.max(p)` prints `np.int64(12870)` instead of `ndplex(12870)`; code that used it as an array is unaffected.
- **C5. `arg_locs` outside the array read 0** (N1, D5). Proposed: zero padding, matching `diag`; positive offsets raise `ValueError`; `arg_locs=None` becomes the default (`[]` still accepted). *Migration:* results change only for `arg_locs` that reach outside the array, which none of the notebook's examples do.
- **C6. `diag` trims padding, not data** (N2, D6). Proposed: the result's length comes from how far the moves stay inside the array, not from where the zeros start; all-zero lines return zeros. *Migration:* results change only where a diagonal ends in genuine zeros (none of the notebook's examples).
- **C7. Small argument fixes** (N4, N6). `edges` accepts any integer type; `nrows < 1` and edges of the wrong length raise `ValueError` with a clear message; the default `dtype` is `np.int64` on every platform; `func` defaults to the builtin `sum`. *Migration:* none.
- **C8. `oeis`** (N3, D7). Proposed: https, a timeout, standard library only; network or format errors print "row i: lookup failed (...)" instead of "no match"; it still prints as before, and also returns a list of `(A-number, name)` pairs, `None` for no match. *Migration:* none for printed output; `x = oeis(...)` now gets a list instead of `None`.
- **C9. Plotting** (F7, N5, D8). Proposed: `diag_as_hist` works on current matplotlib (the rename), computes the normal curve with numpy, and cycles colours; both functions accept `ax=` and return the Axes, and still show the figure by default; `plot_ndplex`'s first argument is renamed `array`. *Migration:* passing the array by keyword (`plot_ndplex(ndplex=p)`) must become `plot_ndplex(p)`; in a notebook the returned Axes prints `<Axes: >` after the plot, as seaborn's do.
- **C10. Docstrings.** State the edge orientation, that `as_tri` returns rather than prints, the zero-padding convention, and the overflow limits.

**Examples notebook (Phase 5)**, noted here so they are not lost: get primes without the gist (or keep it with an offline fallback); use `dtype=object` for the Fibonacci-mod-7 puzzle; replace `np.float128`; print lists with `.tolist()`; fix the nearest-prime edge effect (N8); `pip install ndplex` in the first cell.

---

## 8. Decisions for Phase 2

- **D1. Names.** Distribution `ndplex` (free on 6 Nov 2026; recheck before publishing), import `ndplex`, class `ndplex`, used as `from ndplex import ndplex`. Alternative: a CapWords class (`NDPlex`) with `ndplex` as an alias. *Recommendation:* keep `ndplex`; it is the project's name and keeps every notebook call unchanged.
- **D2. Dependencies.** numpy-only core, matplotlib as the `plot` extra, scipy/seaborn/requests dropped (C2). *Recommendation:* yes.
- **D3. Overflow.** (a) one summary warning per construction (C3); (b) raise `OverflowError` unless the caller opts in; (c) leave numpy's per-operation warnings, now visible. *Recommendation:* (a), plus fixing N12.
- **D4. Derived arrays.** As in C4, or simpler: everything except `ndplex(...)` itself returns a plain `ndarray`. *Recommendation:* C4; slices that print as `ndplex([...])` match the notebook.
- **D5. Out-of-range `arg_locs`.** Zero padding (C5), or keep wrap-around and document it. *Recommendation:* zero padding; the wrap-around depends on loop order.
- **D6. Trailing zeros in `diag`.** Trim by geometry (C6), or keep trimming zeros and document it. *Recommendation:* geometry.
- **D7. `oeis`.** Print and return (C8), or switch to returning only. *Recommendation:* print and return.
- **D8. Plotting.** Return the Axes and keep showing by default (C9); and should `plot_ndplex` draw negative values (today only values > 0 appear)? *Recommendation:* return Axes; draw every non-zero value.
- **D9. Third-party code.** Rewrite `trim_trailing_zeros` (needed for C6 anyway) and the OEIS query (needed for C8) from scratch, keeping the credits in ATTRIBUTION.md as history. That removes the CC BY-SA share-alike question from an MIT package. I'm not a lawyer; this is the cautious route, not legal advice. *Recommendation:* rewrite.
- **D10. NumPy floor.** `numpy>=1.23.5`, as bounded-lognorm, with an explicit int64 default (C7), or require NumPy 2. *Recommendation:* 1.23.5 with explicit int64.

Phase 2 is engineering (package structure and the fixes above), so by the project's rule a Sonnet-class model fits.
