# ndplex — Phase 5: The examples notebook

**Status:** `notebooks/ndplex_examples.ipynb` built and checked here against ndplex 0.1.0 from PyPI; Colab run, oeis cells and link audit pending Ted's Colab runs (§7). The plotting `ImportError` and the README point to the notebook (C13, amended). No release yet: whether these go out as 0.1.1 is Ted's decision (§8).

**Carried over from Phase 4** (PRs #11–#13, master at `ddab8eb`): ndplex 0.1.0 on PyPI (8 Nov 2026, from `v0.1.0` at `2c32bc8`) and Zenodo (concept DOI 10.5281/zenodo.24054477); `oeis` names itself to oeis.org (C14); the suite (194 tests), CI and the publish workflow; the to-do lists in `docs/phase2_package.md` §9, `docs/phase3_ci.md` §8 and `docs/phase4_release.md` §10. `ndplex_array.ipynb` is unchanged and stays as the record of the original work.

**Epistemic labels**, as before. *Run* = observed by running the code here (Linux x86_64, Python 3.13.18, NumPy 2.5.4, matplotlib 3.11.2, seaborn 0.13.2, pandas 3.1.1); true for what was run, not a guarantee beyond it. *Proved* = a short argument given in the text. *Not checked* = could not be run here.

---

## 1. The notebook

- **Built from the original, cell by cell.** All 279 cells of `ndplex_array.ipynb` are carried over in order, except the library cell (now the package), its heading, the old Colab badge and a trailing empty cell. Each carried-over cell records its original position in `metadata["ndplex"]["original_cell"]`, which `tests/notebook_check.py` uses to compare outputs. Ted's text is unchanged apart from the links in §6.
- **New cells** (`metadata["ndplex"]["new"]`): a Colab badge, an introduction, the setup cells (E1), the plotting-helper cell (E2), one check cell (E9), and **Package notes**: short markdown cells, before or after a changed cell, saying what changed and why. 291 cells in all.
- **Network.** Only the eight `oeis` cells need the network (marked by a comment and `metadata["ndplex"]["network"]`). The primes no longer do (E5).

## 2. Changes from the original notebook, with migration notes

Cell numbers are 0-based positions in `ndplex_array.ipynb`, as in `tests/` and the earlier notes.

- **E1. Setup.** `%pip install -q ndplex`, then the imports, `from ndplex import ndplex, oeis`, and a printed version line. `sns.set_theme(style="darkgrid")` is now an explicit line in the notebook (the library cell used to call it on import; C1). `%matplotlib inline` makes each figure appear under its own cell outside Colab too (P5). *Migration:* none for readers; in your own notebooks, set the seaborn theme yourself if you want the old look.
- **E2. Plotting helpers** (D8, C9; audit F1, F7, N5). `plot_ndplex` and `diag_as_hist` are copied from the library cell, with these changes only:
    - `diag_as_hist`: `legend_handles` (`legendHandles` was removed in matplotlib 3.9, so every `normed=True` call failed: 10 cells); colours cycle, so more than six data sets work; the normal pdf is computed with NumPy instead of `scipy.stats.norm`; weights are converted to float (so `dtype=object` diagonals work).
    - `plot_ndplex`: the serif font is set for its own figure (`plt.rc_context`) instead of in `plt.rcParams`, which changed every later plot in the session; non-zero values are drawn, negative ones included (the original drew only values > 0; zeros stay blank because `as_tri` pads with zeros); the first argument is named `array` (it was `ndplex`, which hid the class inside the function).
    - Both still show the figure and return `None`. The drawing geometry is Ted's, unchanged. *Migration:* `plot_ndplex(ndplex=p)` becomes `plot_ndplex(p)` (no notebook cell passes it by keyword).
- **E3. The six overflow cells** (C3; audit F5).
    - 132 and 134 (Sierpinski, divisors 2 and 4): `dtype=object`, so the arrays are exact and no warning is printed; the residues are converted to `int` for the heatmap. The pictures are the same as before (*Run*: 0 of 10 000 residues differ, E9).
    - 136 (divisor 5): kept `int64` on purpose, because the overflow is the puzzle the notebook poses. It now prints the package's one `RuntimeWarning`, which a Package note explains.
    - 208 and 212 (golden ratio, Narayana's cows): `ndplex(50, dtype=object)`. Same values; no warning; Python numbers print as `1.618033988749895`, `1278` and `1149` (the cows cell 214 follows), as the original did, instead of NumPy 2's `np.float64(...)` and `np.int64(...)`.
    - 226 (Fibonacci edges mod 7): `dtype=object`. **The picture changes** in its lower-right corner: in the original, node values overflowed from row + column = 66 on (481 nodes), and 405 of the 2500 cells showed the wrong residue (*Run*, as the audit found). The stripes are genuine.
    - *Migration:* none for values printed. Figures 226 and 264 (E6) change as described.
- **E4. Printing with NumPy 2** (audit §2). Cells 24 and 30 print `np.trim_zeros(row).tolist()`, so the rows print as `[1, 2, 1]` instead of `[np.int64(1), ...]`. Cells 208, 212 and 214 print plain numbers through E3.
- **E5. Primes without the gist** (audit F8). Cell 233 computes the first 1000 primes with `primesfrom2to(8000)[:1000]`, the sieve the original already defined in that cell, and prints a check line (`1000 primes, the last is 7919`, *Run*). The gist is still checked in the link audit (§6), including whether its numbers equal the sieve's. *Migration:* none; the 28 later cells reproduce their outputs.
- **E6. `np.float128` replaced** (audit F8; finding N13). Cell 264 uses `dtype=object`. `float128` does not exist on Windows or Apple-silicon Macs, and `int64` cannot hold the Fibonacci numbers on the top edge (from the 93rd on), so the package raises `OverflowError` for that edge. `primesfrom2to(...).tolist()` gives Python integers. **The picture changes** in columns 94–99 (N13).
- **E7. The nearest-prime edge effect** (audit N8). Cell 276 searches the primes below *twice* the array's maximum (`primesfrom2to(2 * sam.max())`); by Bertrand's postulate there is a prime between n and 2n, so that list includes the nearest prime to every node (*Proved*, given the postulate). Only node (9, 9) changes, 16 → 14: 223 653 is 14 from 223 667 and 16 from 223 637 (*Run*). The 16s at (3, 9) and (9, 3) are genuine (1343, nearest prime 1327).
- **E8. Divide-by-zero in `adj_ratios`** (cell 116). The first ratio is `inf` where a diagonal starts with 0 (cells 121, 123), and the original printed it as `inf` with warnings silenced globally (C1). The function now silences only that division (`np.errstate(divide="ignore")`), with a comment; output is unchanged.
- **E9. A check cell after 138** (new). It answers the notebook's "Curiously, you do not need to make this correction if divisor is a power of 2" with the audit's finding (F5, *Proved*: int64 arithmetic is arithmetic modulo 2^64, so residues modulo powers of 2 survive overflow) and shows it on the 100 × 100 array: 0 residues wrong for divisors 2, 4 and 8; 4081, 4886 and 5169 of 10 000 wrong for 3, 5 and 7 (*Run*).
- **E10. `oeis` cells** use the package's `oeis` (C8, C14). Links print as `https://`; failures print `lookup failed (...)` instead of `no match`. The notebook's own `requests`-based `oeis` is not used. Results depend on oeis.org on the day (§7).

## 3. Package and repository changes

- **C13, amended. The plotting `ImportError` names the examples notebook:** "… A working copy is in the helper cell of the examples notebook, notebooks/ndplex_examples.ipynb: https://github.com/tedteske/ndplex/blob/master/notebooks/ndplex_examples.ipynb". Type and trigger unchanged. *Migration:* none, unless code matched the message text. `tests/test_package.py` checks the new link; restoring the old message fails it (*Run*, 2 failures).
- **README.** A new *Examples notebook* section with an *Open in Colab* badge; the *Plotting* section points to the helper cell. The PyPI page changes only with a release (§8).
- **`tests/notebook_check.py`** (new, on demand like the mutation and differential checks): runs the notebook (or reads one already run, e.g. in Colab: `--executed`) and compares it with the original's saved outputs (§4). **`checks.yml`** gets a third job, *Examples notebook*, which runs it against the branch's code and uploads the executed notebook.
- `CHANGELOG.md` (Unreleased) and `ATTRIBUTION.md` (Phase 5 in tier B; the link audit in the references).

## 4. Verification

- **Run top to bottom here**, in a fresh environment with ndplex 0.1.0 installed from PyPI (`pip install ndplex`, *Run*), and again against the source tree as the CI job does. 23 s.
- **Compared with the original's saved outputs** (`tests/notebook_check.py`, *Run*): **133 of 133** carried-over offline code cells match exactly, text and number of figures. The two intended differences are the ones listed (cell 233's new check line; cell 276, E7). One cell writes to stderr, the intended warning in cell 136. No cell raises. The eight `oeis` cells could not reach oeis.org from here (*Not checked*; §7).
- **The helper fixes, checked directly** (`check_helpers` in the same script, *Run*): `diag_as_hist(normed=True)` runs with 8 data sets and 6 cycling colours; the first legend handle is black; the curve equals the normal pdf (relative error < 1e-12) and integrates like one (checked with `math.erf`); `plot_ndplex` leaves `font.family` alone, uses serif in its figure, draws the 30 non-zero nodes of a 6 × 6 array with negative values and none of its zeros, and draws the 15 nodes of a 5-row triangle.
- **Mutation check of the checker** (*Run*): 16 deliberate faults, each caught: `legendHandles` restored; the global font restored; colour cycling removed; a five-colour cycle; only positive values drawn; zeros drawn; two wrong pdf formulas; the legend handle not black; a changed digit in two printed results; a lost figure; an extra warning; the expected warning missing; E7 reverted; a cell that raises.
- **Test suite:** 194 passed (*Run*), including the amended C13 test.

## 5. New findings

- **N13. The original "Alien invasion" heatmap (cell 264) was partly wrong.** It used `float128`, which on Linux x86 is 80-bit extended precision with a 64-bit significand, so integers above 2^64 are rounded. The Fibonacci numbers on the top edge pass 2^64 at column 93, and five of them (columns 93, 94, 96, 97, 99) were stored with the wrong parity. Since the rule is `(x[0] + x[1]) % 2`, the error spreads down: 369 of the 9801 plotted cells, all in columns 94–99, differ from the exact array (*Run*, comparing the `float128` and `dtype=object` arrays here). The rest of the picture is exact. (The audit's F8 noted only that `float128` is not portable.)
- **P5. Figures outside Colab.** Run with `nbclient` and the current `ipykernel` and `matplotlib_inline`, figures drawn by seaborn without `plt.show()` were not shown under their own cell but carried over to the next `plt.show()` (*Run*: 15 cells with the wrong figure count). `%matplotlib inline` in the setup cell fixes it; Colab already behaves this way (the original's saved outputs).

## 6. Link audit

Every link in `ndplex_array.ipynb` and `ATTRIBUTION.md`, and the new ones in the examples notebook (44 URLs). This environment cannot reach most of these sites (its network allows only a few hosts), so three were checked here by fetching them and the rest go to the Colab check (§7).

**Checked here** (8 Nov 2026):

- AMS Feature Column, *From Pascal's Triangle to the Bell-shaped Curve*: live at `https://www.ams.org/publicoutreach/feature-column/fcarc-normal` (Tony Phillips, May 2010). The examples notebook links the https address and names the article.
- Allouche and Johnson, *Narayana's Cows and Delayed Morphisms* (JIM 96): a copy is live on OEIS at `https://oeis.org/A000930/a000930.pdf` (deposited in HAL as hal-02986050). The examples notebook links it in place of `http://jim.afim-asso.org/jim96/actes/Allouche.ps`, whose status is in the Colab check.
- Iowa State REU, *Pascal's triangle modulo n* (`orion.math.iastate.edu/.../modupasc.htm`): the address is still indexed by search engines, but its robots.txt blocks fetching, so its content was not checked. The examples notebook keeps it and adds Wikipedia's *Sierpiński triangle* as a second source.

**Changed in the examples notebook regardless of the check:** OEIS links `http://` → `https://`; the Amazon link for Green (2015) replaced by the full citation and the Google Books page (the one in ATTRIBUTION.md).

**Pending the Colab check** (`phase5_link_check.ipynb`, not committed; results to be recorded here): all 44 URLs, each fetched naming ndplex and, if refused, as a browser; and whether the gist still holds the first 1000 primes, equal to the sieve's.

## 7. What Ted checks in Colab

1. **`notebooks/ndplex_examples.ipynb`:** upload it, Runtime → Run all, then File → Download → .ipynb and attach it. `tests/notebook_check.py --executed` will compare it as above. What to look for meanwhile:
    - the setup cell prints `ndplex 0.1.0`;
    - no cell shows an error; one cell (divisor 5) shows one `RuntimeWarning`;
    - the eight `oeis` cells print A-numbers with `https://oeis.org/...` links. Expected rows are in the original notebook's outputs; OEIS names may have been edited since 2024, and a different A-number for a row is possible where OEIS now has a better match, so those differences are reported, not treated as errors. `lookup failed (...)` on every row would mean oeis.org refused the request.
2. **`phase5_link_check.ipynb`:** Run all, download, attach. The summary cell lists links that did not answer 200; the last cell says whether the gist matches the sieve.

## 8. Decision for Ted

- **0.1.1 or wait.** The C13 message and the README's PyPI page change only with a release. Recommendation: release 0.1.1 after this PR is merged, because the 0.1.0 message sends users to the original notebook, whose `diag_as_hist` fails on matplotlib ≥ 3.9. This PR leaves the version at 0.1.0 and lists the changes under *Unreleased*; a release would be a separate small PR (`0.1.1.dev1` on TestPyPI first, as in Phase 4).

## 9. For later

- Record the Colab results (§7) here and in ATTRIBUTION.md; replace any dead link found there.
- If 0.1.1 is released: the version bump, TestPyPI check, release notes, and the post-release PR with its Zenodo DOI, as in Phase 4.
