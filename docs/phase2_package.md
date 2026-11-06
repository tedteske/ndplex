# ndplex — Phase 2: Package structure and API cleanup

**Status:** done, pending review (PR). `src/ndplex` is a working package with the fixes approved from the Phase 1 audit. Nothing is released; the version is `0.1.0.dev0`.

**Carried over from Phase 1** (PR #8): `docs/phase1_audit.md` (findings F1–F9 and N1–N12, proposed changes C1–C10, decisions D1–D10), the regression suite (126 passing, 12 strict xfails), `tests/mutation_check.py` and `ATTRIBUTION.md`.

**Epistemic labels**, as in Phase 1. *Run* = observed by running the code here; true for what was run, not a guarantee beyond it. *Numerical* = checked over a stated range, not proved. *Argued* = reasoned from the code, not tested exhaustively. *Not checked* = could not be run here.

**Environments** (*Run*): Python 3.13.18 with NumPy 2.5.4 (current), and Python 3.10.20 with NumPy 1.23.5 (the declared minimum). Linux only; macOS and Windows are for the Phase 3 CI.

---

## 1. Decisions

Approved by Ted on 6 Nov 2026, as recommended in the audit, with three amendments and one further decision:

- **D1. Names.** Distribution, module and class are all `ndplex`; `from ndplex import ndplex` as in the notebook. *Amendment:* the implementation modules are private (`_core.py`, `_oeis.py`), so that importing `ndplex._oeis` cannot replace the function `ndplex.oeis` with a module (the bug bounded-lognorm fixed in its Phase 4).
- **D2. Dependencies.** NumPy only. scipy, seaborn and requests are dropped.
- **D3. Overflow.** (a): one summary warning per construction, plus the fix for N12.
- **D4. Derived arrays.** As in C4. *Amendment:* pickling keeps the attributes, but a `func` that cannot itself be pickled (a lambda) comes back as `None`, so arrays built with a lambda still pickle, as they did in the notebook.
- **D5.** `arg_locs` outside the array read 0.
- **D6.** `diag` trims by geometry.
- **D7. `oeis`.** *Amendment:* the default prints and returns `None`, as the notebook did; `quiet=True` returns the results without printing. (Printing and also returning a list would have echoed the list under every notebook cell that ends with `oeis(...)`.)
- **D8. Plotting: left out of the package** (Ted's decision, option (a)). `plot_ndplex` and `diag_as_hist` move to the examples notebook as a helper cell in Phase 5, with the audit's fixes applied there. Reasons: the package's value is the array; plotting is the part that already broke on a matplotlib change (F7); adding `ndplex.plot` later breaks nothing, removing it later would.
- **D9.** `trim_trailing_zeros` and the OEIS query are rewritten from scratch; the credits stay in ATTRIBUTION.md as history.
- **D10.** `numpy>=1.23.5`, with `np.int64` as the default dtype.

---

## 2. Package layout

- `src/ndplex/__init__.py`: exports `ndplex`, `oeis` and `__version__`. `oeis` is loaded on first use (a module `__getattr__`), so `import ndplex` imports only NumPy. `plot_ndplex` and `diag_as_hist` raise `ImportError` with a message pointing to the examples notebook.
- `src/ndplex/_core.py`: the class. NumPy only.
- `src/ndplex/_oeis.py`: `oeis`. Standard library only (`urllib`).
- `pyproject.toml`: as bounded-lognorm's (hatchling, version read from `__init__.py`, `requires-python >=3.10`, PEP 639 license fields, Core Metadata 2.4, a `test` dependency group). The only dependency is `numpy>=1.23.5`. There are no extras.
- `CHANGELOG.md`: started, with an "Unreleased" section.
- `ndplex_array.ipynb` is untouched; it is Phase 5's.

---

## 3. Changes from the notebook, with migration notes

Every value the notebook computes is unchanged: Suites A–D (the notebook's printed results) pass without edits apart from expecting the new overflow warning in three tests (*Run*). The differential check (§6) compares the package with the notebook's code directly.

**C1. No import side effects** (F1).
- Importing no longer calls `warnings.simplefilter('ignore')` or `sns.set(style="darkgrid")`.
- *Migration:* warnings now appear, notably overflow (C3). For the old plot look, add `import seaborn as sns; sns.set_theme(style="darkgrid")` to the notebook.

**C2. Lighter imports** (F2).
- `import ndplex` loads NumPy only; `oeis` loads `urllib` on first use.
- *Migration:* `from ndplex import ndplex, oeis` works as before. `from ndplex import plot_ndplex, diag_as_hist` raises `ImportError`: copy the functions from the examples notebook (Phase 5). 24 notebook cells use them (cells 33–43, 108, 109, 149, 154, 158, 160, 185–199, 206, 221, 230).

**C3. Overflow is reported** (F5, N12; decision D3a).
- If any node overflows the dtype, construction issues one `RuntimeWarning`, for example: *ndplex: node values overflowed int64 from node (24, 49) on (in generation order); that node and those computed from it are wrong. Use dtype=object for exact integers, or reduce inside func (e.g. a modulus).* The node named is the first wrong node in generation order (row by row), which is not the node with the smallest i + j: for `ndplex(70)` the first wrong i + j is 67, but row 24 is reached first. The warning points at the caller's line. Values are unchanged (wrapped modulo 2^64), so the powers-of-2 residues still hold.
- How: node generation runs under `np.errstate(over="raise")`; a node whose `func` call overflows is recomputed with overflow ignored, so its value is what NumPy would have stored. Float overflow to `inf` is reported the same way.
- `dtype=object` is the exact route; `diag` and `as_tri` now pad object arrays with Python int zeros, so their sums are exact past 2^63 (`ndplex(100, dtype=object).as_tri(sums=True)[-1] == 2**99`, *Run*).
- *Limits* (*Argued*): only overflow that NumPy signals is caught. A `func` that converts to Python ints and returns a value too large for int64 already raised `OverflowError` on assignment, and still does.
- *Migration:* none for results. Six notebook cells will now show one warning each, because they build arrays that overflow: 132 and 134 (Sierpinski mod 2 and 4; results correct), 136 (mod 5; results wrong in the corner, as the notebook says), 208 and 212 (golden ratio and Narayana's cows from `ndplex(50)`; the diagonals used are exact) and 226 (Fibonacci edges mod 7; partly overflowed, F5). In Phase 5 they can use `dtype=object` or smaller arrays.

**C4. Arrays derived from an ndplex keep working** (F4; decision D4).
- `nrows` is now read from the shape (a property); it is `None` when the sides differ, as for `p[1:]`.
- `diag` uses only the shape, so it works on slices, arithmetic results, copies and unpickled arrays, including non-square slices (`ndplex(5)[1:].diag()` is `[1, 3, 10, 35]`).
- `edges`, `func` and `arg_locs` are carried through views, copies and arithmetic as a record of how the array was built. They are not used after construction, so on a slice they describe the parent array.
- `as_tri` needs equal sides and raises `ValueError` otherwise.
- Reductions (`p.sum()`, `np.max(p)`) return plain NumPy scalars instead of 0-d ndplex arrays.
- Pickling keeps `edges`, `func` and `arg_locs`; an unpicklable `func` (a lambda) comes back as `None`.
- *Migration:* `np.max(p)` prints `np.int64(70)` instead of `ndplex(70)`; values are unchanged.

**C5. `arg_locs` outside the array read 0** (N1; decision D5).
- A relative location that falls outside the array (a negative coordinate) reads 0, as `diag` does, instead of wrapping around to the far side. Positive offsets raise `ValueError`; non-integer offsets raise `TypeError`. `None` still means "on the edge". The default is `arg_locs=None`; `[]` is still accepted.
- *Migration:* results change only for `arg_locs` that reach outside the array, e.g. `[[-1, 0], [0, -1], [-1, -2]]`, where node (1, 1) is now 2 instead of 3. None of the notebook's examples reach outside the array. The default 3-D faces were already zero-padded in effect (they read uncomputed zeros); now that holds by construction rather than by loop order.

**C6. `diag` ends where the moves leave the array** (N2; decisions D6, D9).
- The result's length along each axis is set by the last position inside the array, not by where the zeros start. Genuine trailing zeros are kept; an all-zero line returns zeros; a line starting outside the array returns an empty array. Positions outside the array before the end still read 0, as before. `as_tri` builds on the same rule, so arrays with genuine zeros (such as `edges=(c, -c)`) now give a triangle instead of `IndexError`.
- A `loc` with fewer coordinates than dimensions still selects whole sub-arrays (layers or lines), as the docstring's "node or 1D array" says, and the default move still steps one along each axis `loc` fixes; pinned by new tests.
- A move with more coordinates than `loc` now raises `ValueError`; the notebook silently ignored the extra coordinates.
- For a 1-node array, a partial `loc` now gives a 0-d result, as a full `loc` already did; the notebook gave shape (1,) or (1, 1), because its zero padding was squeezed together with the data.
- *Migration:* results change only where a diagonal ends in genuine zeros, e.g. row 1 of `ndplex(8, func=lambda x: x[0] - x[1])` now has 8 values, not 7. None of the notebook's examples do. Drop any extra move coordinates.

**C7. Argument handling** (N4, N6, F3).
- `edges` accepts any integer type (`np.int64(3)`). `nrows < 1`, `edges < 1`, `edges=()`, an edge of the wrong length, an `arg_loc` of the wrong length, and `diag` locations or moves of the wrong length raise `ValueError` with a message.
- The default dtype is `np.int64` on every platform (it was the platform int, int32 on Windows with NumPy 1.x, where overflow starts at i + j = 34).
- `func` defaults to the builtin `sum` (same results as `lambda x: sum(x)`, and picklable).
- `edges=n` is stored as a tuple of Python ints, `(1, 1, 1)`, instead of NumPy ints; it compares equal.
- *Migration:* code that caught `IndexError` for `ndplex(0)` or a positive offset must catch `ValueError`.

**C8. `oeis`** (N3; decisions D7, D9).
- Requests go to `https://oeis.org/search` with a timeout (default 10 s), using the standard library.
- A network failure or an answer not in OEIS's text format prints `lookup failed (...)` on that row's line instead of `no match`.
- `quiet=True` prints nothing and returns a list, one entry per row: `(A-number, name)`, or `None` for no match. In quiet mode failures raise (`OSError` or `ValueError`).
- 3-D input raises `ValueError` (the notebook sent garbage queries).
- *Migration:* printed links start `https://` instead of `http://`; otherwise printed output is unchanged. The 8 OEIS cells (16, 70, 80, 100, 219, 224, 241, 262) print the same apart from that.

**C9. Plotting.** Left out of the package (D8). The fixes listed in the audit for `plot_ndplex` and `diag_as_hist` (the `legend_handles` rename, no global font change, colour cycling, drawing negative values) move to the Phase 5 helper cell.

**C10. Docstrings.** The class docstring states the edge orientation (edge k lies along axis k; in 2-D `edges[0]` fills column 0, `edges[1]` row 0, and the last edge wins at the origin), the zero-padding rule for `arg_locs`, and the overflow limits (default 2-D exact for i + j ≤ 66, 3-D for i + j + k ≤ 43). `as_tri` says it returns rather than prints, and that a genuine zero in a cross-section looks like padding.

---

## 4. The twelve expected failures

Each strict xfail lost its marker in the commit that made it pass (the package commit, which contains all the fixes).

Turned into passes (10):

- `test_import_leaves_warning_filters_alone` (F1, C1)
- `test_import_leaves_matplotlib_style_alone` (F1, C1)
- `test_import_needs_only_numpy` (F2, C2; now also checks that pandas, matplotlib and `ndplex._oeis` are not imported)
- `test_diag_works_on_a_slice`, `test_diag_works_after_arithmetic`, `test_pickle_round_trip_keeps_methods_working` (F4, C4)
- `test_object_dtype_sums_past_int64` (N12, C3)
- `test_diag_of_all_zero_line`, `test_as_tri_of_all_zero_array` (N2, C6)
- `test_edges_accepts_numpy_int` (N4, C7)

Removed with plotting (2): `test_plot_ndplex_leaves_global_font_alone` (F1) and `test_diag_as_hist_normed_runs` (F7). They go with Suite F (`tests/test_plotting.py`, 10 tests). The Phase 5 notebook run becomes their check.

`test_current_*` tests whose behaviour changed were rewritten under new names, each with its migration note in the docstring: result types (C4), overflow (C3), arg_locs wrap-around (C5), the genuine trailing zero (C6), oeis "no match" on failure (C8), edge cases (C7), and the defaults (F3, C7). Those whose behaviour did not change keep their `test_current_` names.

---

## 5. The test suite

Run with `pip install -e . pytest` and then `pytest`. Result: **164 passed, 0 xfail, about 2 s**, on both environments above, also with `-W error` on NumPy 2.5.4 (*Run*). No test uses the network. matplotlib is optional: the one test that needs it skips without it.

- `tests/_impl.py` now imports the installed package (as bounded-lognorm's tests do), so a packaging mistake fails the tests. `NDPLEX_IMPL_PATH` points it at another copy of the package (used by the mutation check).
- Suites A–D (the notebook's results) are unchanged apart from expecting the overflow warning in three tests, and one new test pinning `diag` with a partial `loc`.
- Suite E (`test_oeis.py`) stubs the module's one network function instead of `requests.get`, and adds `quiet=True`, timeouts, failure reporting and UTF-8 decoding.
- Suite G (`test_known_issues.py`) as in §4, plus tests for overflow (first node named, 3-D, float, no false alarms), pickling with a lambda, the attributes on derived arrays, thin slices, object-dtype triangles, and argument messages.
- New `test_package.py`: public names, lazy loading of `oeis`, no submodule shadowing the function, the removed plotting names.
- `tests/ndplex_original.py` stays as the record of the notebook's code (`test_original_copy.py` still checks it against the notebook) and as the reference for the differential check.

---

## 6. Differential check against the notebook's code

`tests/differential_check.py` compares the package with `tests/ndplex_original.py` where nothing should change: construction in 1–4 dimensions with various edges, funcs, dtypes and in-range arg_locs; up to 150 random `diag` calls (one to four moves, with and without `sum_axis`) on each of 14 arrays from 2-D to 5-D without genuine zeros; `as_tri` for every start and end; and every partial `loc` with the default move. Calls where the original raises are skipped. Result (*Numerical*, seed 1): **all equal, 4,822 comparisons.** It needs the original's imports (scipy, seaborn, requests, matplotlib), so it runs on demand, not in pytest.

### 6a. Review of `diag` (requested before merge)

The line-building and line-ending logic was checked against the notebook's code, case by case (*Run*, both implementations side by side) and by reading:

- **Axis order with several moves.** Axis 0 steps the last move and the last axis the first move, so with two moves `result[a, b]` is the node at `loc + a * move[1] + b * move[0]`. This is unchanged from the notebook, and is what the Fibonacci and Narayana examples rely on (`move=[(-2, 1), (1, 0)]`, `sum_axis=1` sums each steep diagonal).
- **Number of steps.** Each move takes as many steps as the array's longest side, as in the notebook (`nrows`). Only a degenerate pair of moves, such as opposite moves, could stay inside longer than that; those are capped the same way as before.
- **Outside positions.** Positions with any coordinate below 0 or past the side read 0. A negative `loc` is outside, not counted from the end, as in the notebook. Only trailing outside positions are dropped. Positions outside the array before the last inside one stay as zeros: a line that starts outside and enters keeps its leading zeros, and a 2-move cross-section is cut to its bounding box. `as_tri` relies on this.
- **Line ending.** This is the one intended change (C6): the length along each axis is the last position with any node inside the array. On arrays without genuine zeros this gives the same lengths as the notebook's zero-trimming; the differential check confirms it.
- **One bug found and fixed.** With a `loc` that fixes only some axes and no `move`, the first draft built a default move for every axis and then raised `ValueError`. The notebook stepped along the axes `loc` fixes (`p.diag(loc=(1,))` gives layers 1, 2, 3). The default is now one step along each axis `loc` fixes, pinned by tests and by the differential check.
- **Two edge cases decided rather than copied** (§3, C6): a move longer than `loc` raises instead of being silently cut, and a 1-node array with a partial `loc` gives 0-d.
- **Unchanged forms of input.** `loc` and `move` may be lists, tuples or numpy arrays. A single move may be given as a flat list (notebook cell 230: `move=[-1, 1]`). A zero move repeats the start node once per step, as before.
- **Higher dimensions** (*Numerical*). `diag` was checked against a brute-force reference written from the definition with plain loops: 1,881 random calls on 4-D and 5-D arrays, including partial `loc`s, `loc`s outside the array, one to four moves, non-cubic slices, a side of length 1, and arrays with many genuine zeros. All agree. Moves along unit axes return exactly numpy's slices (e.g. `p[:, 2, :, :, 0]` of a 5-D array). A smaller version of the reference check is in the suite (`test_diag_matches_reference_in_4d_and_5d`, 5 arrays).
- **`as_tri` in 4-D and up: right values, sheared layout** (*Numerical*, 3-D to 6-D). Each layer holds every multinomial coefficient of its order exactly once, and the layer sums are d^r. In 2-D and 3-D each layer is a left-justified triangle. From 4-D up it is not: in 4-D, layer r occupies the positions (a, b, c) with a ≤ b and b + c ≤ r, instead of a + b + c ≤ r. The cause is the move pattern, unchanged from the notebook. The first two moves take a step from the layer's pivot axis (axis d − 2), but from the third move on each takes it from the next axis instead; in 4-D the third move is (1, −1, 0, 0) rather than (1, 0, −1, 0). Every node still appears once, because the map between the two layouts is one-to-one. This was not introduced in Phase 2. The notebook uses 4-D `as_tri` only with `sums=True`, which is unaffected. **Decision pending (Ted):** keep the notebook's layout and document it, or switch to left-justified layers. The switch changes no 2-D or 3-D result and no sums, but 4-D and higher layers would be arranged differently (*Run*: the alternative moves give left-justified 4-D and 5-D layers with the same values).

---

## 7. Mutation check against the package

`tests/mutation_check.py` now mutates `src/ndplex/_core.py` and `src/ndplex/_oeis.py` (every top-level class and function), runs the suite against a copy of the package containing the change, and records whether a test fails. The operators are those of Phase 1, plus `&`.

Result (*Run*, 6 Nov 2026): **459 mutants (375 in `_core.py`, 84 in `_oeis.py`); 448 killed, 11 survived, all 11 equivalent.** The first run found gaps, closed in this phase:

- Redundant code (*Argued* equivalent, then removed): a separate zero-padding helper for object arrays (`np.zeros(..., dtype=object)` already gives Python int zeros, on NumPy 1.23.5 and 2.5.4, *Run*), a dtype branch for the fill value, an `operator.index` on `nrows`, and a `tuple()` conversion.
- Untested checks, now tested: `edges=()`, the exact text of every argument error, the overflow warning's full text and the line it points to (`stacklevel`), `arg_locs` carried through copies, non-integer `arg_locs` offsets, object-dtype triangles (whose padding was not checked), `diag` on slices with a side of length 1, and the network function in `_oeis.py`, with undecodable bytes.
- One real gap in the line-ending rule: deleting the squeeze of the inside/outside mask survived. It matters only when a sub-array line passes through a side of length 1; `test_diag_through_a_slice_with_a_side_of_one` now kills it (re-run).

The 11 equivalent mutants (*Argued*: same behaviour on every valid input):

- `nrows`: deleting the final `return None` (the implicit return is `None`); `s[0]` → `s[-1]` in the property, twice (all sides are equal there).
- `as_tri`: `a.shape[0]` → `a.shape[1]` or `a.shape[-1]`, in the equal-sides check and in the default `end`, four mutants (the sides are equal by then).
- `__array_wrap__`: the default of `return_scalar` flipped (the parameter is accepted for NumPy 2's signature but not used).
- `diag`: the placeholder index for positions outside the array, `0` → `-1` (both are valid indices and those values are then set to 0; `0` → `1` is killed by the thin-slice test); `move[0]` → `move[-1]` in the scalar check (as in Phase 1).
- `as_tri`: `moves[0] * -1` → `moves[0] / -1` (as in Phase 1: the float result is stored back into an integer array).

Run time: about 8 minutes on 3 parallel jobs here.

---

## 8. Not checked

- **The live OEIS.** This sandbox cannot reach oeis.org. Still unknown: whether today's text format is the one the parser expects (the `%N` line, and the greeting line that marks a well-formed "no results" answer), and whether oeis.org accepts urllib's default User-Agent. If it doesn't, every row will print `lookup failed (HTTP Error 403...)`, not a false "no match". Ted can check in Colab after installing from TestPyPI: `oeis(ndplex(5))` should print five A-numbers.
- **macOS, Windows, Colab.** Phase 3's CI covers macOS and Windows; Phase 5's notebook run covers Colab.

---

## 9. For later phases

- **Phase 3 (tests and CI):** `tests.yml` as bounded-lognorm's. The minimum-dependency job is Python 3.10 with NumPy 1.23.5 (passes here); add matplotlib to one job so the style test runs.
- **Phase 4 (packaging):** set the version to 0.1.0; rewrite README.md (it still copies the notebook's docstrings and is the PyPI page); recheck that `ndplex` is free on PyPI (it was on 6 Nov 2026). Cite Green (2015), *The Simplex, Duplex and Pascal's Triangles*, as a general source in the README and in `CITATION.cff` `references` (Ted's request; already in ATTRIBUTION.md).
- **Phase 5 (examples notebook, `notebooks/ndplex_examples.ipynb`):** the name the `ImportError` message already points to.
    - `pip install ndplex` in the first cell.
    - A helper cell with `plot_ndplex` and `diag_as_hist`, fixed: `legend_handles`, no global font, colour cycling, negative values drawn, normal pdf in NumPy.
    - The six overflow cells (C3): `dtype=object` or smaller arrays, or a note on the warning.
    - Earlier audit items: primes without the gist, `np.float128` replaced, `.tolist()` for printing, the nearest-prime edge effect (N8).
