# ndplex — Phase 5: The examples notebook

**Status:** `notebooks/ndplex_examples.ipynb` built and checked against ndplex 0.1.0 from PyPI, here and in Colab (9 Nov 2026, §4); oeis cells and link audit done (§4, §6). The plotting `ImportError` and the README point to the notebook (C13, amended). Merged (PR #14). Released as ndplex 0.1.1 on 10 Nov 2026 (UTC), on PyPI and Zenodo; the release record is §11.

**Carried over from Phase 4** (PRs #11–#13, master at `ddab8eb`): ndplex 0.1.0 on PyPI (8 Nov 2026, from `v0.1.0` at `2c32bc8`) and Zenodo (concept DOI 10.5281/zenodo.24054477); `oeis` names itself to oeis.org (C14); the suite (194 tests), CI and the publish workflow; the to-do lists in `docs/phase2_package.md` §9, `docs/phase3_ci.md` §8 and `docs/phase4_release.md` §10. `ndplex_array.ipynb` is unchanged and stays as the record of the original work.

**Epistemic labels**, as before. *Run* = observed by running the code here (Linux x86_64, Python 3.13.18, NumPy 2.5.4, matplotlib 3.11.2, seaborn 0.13.2, pandas 3.1.1); true for what was run, not a guarantee beyond it. *Proved* = a short argument given in the text. *Not checked* = could not be run here.

---

## 1. The notebook

- **Built from the original, cell by cell.** All 279 cells of `ndplex_array.ipynb` are carried over in order, except the library cell (now the package), its heading, the old Colab badge and a trailing empty cell. Each carried-over cell records its original position in `metadata["ndplex"]["original_cell"]`, which `tests/notebook_check.py` uses to compare outputs. Ted's text is unchanged apart from the links in §6.
- **New cells** (`metadata["ndplex"]["new"]`): a Colab badge, an introduction, the setup cells (E1), the plotting-helper cell (E2), one check cell (E9), and **Package notes**: short markdown cells, before or after a changed cell, saying what changed and why. 292 cells in all.
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
- **E10. `oeis` cells** use the package's `oeis` (C8, C14). Links print as `https://`; failures print `lookup failed (...)` instead of `no match`. The notebook's own `requests`-based `oeis` is not used. Results depend on oeis.org on the day (§4).
- **E11. A note after cell 219** (new, after the Colab run). OEIS now returns A005709 for row 5 where it returned A005708 in 2024 (finding N14); the note explains why and which is meant. The cell is unchanged.
- **E12. Links** (§6): the dead Iowa State link in cell 131 is replaced by Wikipedia's *Sierpiński triangle*; OEIS and ColorBrewer links use `https://`; cells 145, 183 and 211 add the full citation (and, for 145 and 211, a second copy) to links that still work.

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
- **Run in Colab by Ted** (9 Nov 2026; ndplex 0.1.0 from PyPI, NumPy 2.4.6), then compared here with `tests/notebook_check.py --executed`: the same result as here, **133 of 133** offline cells match, the same two intended differences, one intended warning (cell 136), no errors, and the helper checks pass (*Run* in Colab, compared here).
- **The eight `oeis` cells** (Colab, 9 Nov 2026): every row found a match, with `https://` links. Six cells print exactly what the original saved. Two differ because OEIS changed, not the package: in cell 224, OEIS has renamed A204263's formula from f(i,j) to T(i,j); in cell 219, row 5 returns A005709 instead of A005708 (N14).

## 5. New findings

- **N13. The original "Alien invasion" heatmap (cell 264) was partly wrong.** It used `float128`, which on Linux x86 is 80-bit extended precision with a 64-bit significand, so integers above 2^64 are rounded. The Fibonacci numbers on the top edge pass 2^64 at column 93, and five of them (columns 93, 94, 96, 97, 99) were stored with the wrong parity. Since the rule is `(x[0] + x[1]) % 2`, the error spreads down: 369 of the 9801 plotted cells, all in columns 94–99, differ from the exact array (*Run*, comparing the `float128` and `dtype=object` arrays here). The rest of the picture is exact. (The audit's F8 noted only that `float128` is not portable.)
- **N14. Ten terms do not identify row 5 of cell 219.** Row 5 is 1, 1, 1, 1, 1, 1, 2, 3, 4, 5, which appears in A005708 (from its first term) and in A005709 (from its second), so the search returns whichever OEIS ranks first; that changed between 2024 and 2026. Row *k* of that array follows a(n) = a(n-1) + a(n-k-1) (*Run*, all ten rows), so row 5 is A005708, as in A141539. From 13 terms on, only A005708 contains the row (*Run*, rows of 10 to 19 terms). The other nine rows came back as before.
- **P5. Figures outside Colab.** Run with `nbclient` and the current `ipykernel` and `matplotlib_inline`, figures drawn by seaborn without `plt.show()` were not shown under their own cell but carried over to the next `plt.show()` (*Run*: 15 cells with the wrong figure count). `%matplotlib inline` in the setup cell fixes it; Colab already behaves this way (the original's saved outputs).

## 6. Link audit

Every link in `ndplex_array.ipynb`, `ATTRIBUTION.md` and the examples notebook: 44 URLs. Each was fetched in Colab by `phase5_link_check.ipynb` (run by Ted, 9 Nov 2026; not committed): first with a header naming ndplex, then, if refused, as a browser. A few were also fetched from here (8 Nov). *Run*, true for those networks on those days.

39 of the 44 answered 200, but one of those (Iowa State) only after redirecting to an unrelated page. So: 38 live, 1 dead, and 5 refused (the four Stack Overflow links, and the AMS article's old `http://` address, which works at `https://`). Ted then opened the four Stack Overflow links in a browser, and all four work (9 Nov 2026), so 42 of the 44 are live.

**Live (38):**

- All 14 OEIS sequences linked (16 URLs: two are also linked as `http://`, which redirects to `https://`), `eishelp1.html`, and the Narayana's cows PDF on OEIS (`https://oeis.org/A000930/a000930.pdf`).
- Wikipedia (5 articles), seaborn's *Choosing color palettes*, the oeis package by Andrew Walker on GitHub, Ted's repository pages, the Colab badge and both Colab links.
- ColorBrewer: both `http://` links redirect to `https://colorbrewer2.org/`. The part after `#` (the scheme) is read by the page itself, so it still works.
- Green (2015) on Amazon and on Google Books.
- AMS Feature Column at `https://` (Tony Phillips, May 2010). The original's `http://` address answered 403 to both requests from Colab, so the examples notebook uses `https://`.
- Allouche and Johnson, `http://jim.afim-asso.org/jim96/actes/Allouche.ps`: live (PostScript). I had replaced it with the OEIS PDF before this check; the examples notebook now keeps Ted's link and adds the PDF as a copy.
- The primes gist (its page and its raw file): live, and its 1000 numbers equal `primesfrom2to(8000)[:1000]` exactly (*Run* in Colab). So E5 changes nothing in the results.

**Dead (1):**

- `http://orion.math.iastate.edu/reu/oldREU/modupasc.htm` (Iowa State REU, *Pascal's triangle modulo n*) redirects to the Iowa State mathematics department's home page. The page is gone. Search finds other old REU files under `reu.math.iastate.edu/oldREU/`, but I could not fetch that address for this page from here (*Not checked*). The examples notebook replaces the link with Wikipedia's *Sierpiński triangle* and says the original is no longer online.

**Refused automated requests, live in a browser (4):** the four Stack Overflow links (questions 2068372, with answer 3035188 for `primesfrom2to`, 48817036 and 55917328) answered 403 to both requests. Stack Overflow refuses many automated requests, and question 2068372, *Fastest way to list all primes below N*, appears in Stack Overflow archive copies from 2021 and 2023. Ted opened all four in a browser on 9 Nov 2026, and they work. They are unchanged in the examples notebook.

**Changes in the examples notebook** (E12): the Iowa State link replaced; `http://` → `https://` for OEIS, ColorBrewer and the AMS article; full citations added for Green (2015), the AMS article and Allouche and Johnson.

## 7. Colab checks (done)

- `notebooks/ndplex_examples.ipynb`, run by Ted in Colab on 9 Nov 2026 and compared here (§4).
- `phase5_link_check.ipynb`, run by Ted in Colab on 9 Nov 2026 (§6).
- The notebook changed after the Colab run in its text only: E11, E12, and the link changes in §6. No code cell changed, so the comparison still holds; a re-run here gives the same result (*Run*).

## 8. Decision: release 0.1.1

Ted, 9 Nov 2026: merge PR #14 (merged as `1bac08e`) and release 0.1.1, so that the PyPI page and the plotting `ImportError` point to the examples notebook.

## 9. For later

- Nothing open from Phase 5.

## 10. Releasing 0.1.1

**The release PR** (#15, merged as `986a882`) sets `__version__` to 0.1.1, `version: 0.1.1` in `CITATION.cff` (`date-released` comes back in the post-release PR, as in Phase 4), and the CHANGELOG heading *0.1.1 (2026-11-09)*. It changes the version test to 0.1.1, and adds `test_release_metadata_matches_version`: `CITATION.cff` and the latest CHANGELOG heading must name the package's version. Without the test change, the publish workflow would have failed at the suite (*Run*: the version test failed against the 0.1.1 wheel). Changing each of the three version strings in turn fails the new test (*Run*).

**No TestPyPI dry run this time.** The package's code differs from 0.1.0 only in the `ImportError` message (`git diff v0.1.0 master -- src/`). The publish path (OIDC upload, the `pypi` approval, Zenodo) worked for 0.1.0, and the build, tag check and suite run again before the approval point. Replayed here (*Run*): the build, `twine check --strict` (both files pass), the tag check (accepts `v0.1.1`, rejects `v0.1.0`), and the suite against the wheel in a fresh environment.

**Steps (Ted):**

1. **Release:** Releases → Draft a new release → *Choose a tag* → type `v0.1.1` → *Create new tag on publish*, target `master`; title `ndplex 0.1.1`; paste the release notes below; tick *Set as the latest release*; *Publish release*.
2. **Approve:** Actions → the publish run → *Review deployments* → tick `pypi` → *Approve and deploy*.
3. Tell Claude, with the 0.1.1 DOI from the Zenodo record. Claude checks a clean install from PyPI and opens the PR that records the release.

**Release notes:**

> ndplex 0.1.1 adds an examples notebook, `notebooks/ndplex_examples.ipynb`: the original notebook's examples, run on the package installed from PyPI, with working copies of the plotting helpers `plot_ndplex` and `diag_as_hist`. Open it in Colab from the README.
>
> The `ImportError` raised by `from ndplex import plot_ndplex` (or `diag_as_hist`) now points to that notebook instead of the original one. Nothing else in the package changed. Details: CHANGELOG.md and docs/phase5_examples.md in the repository.

## 11. Release record: 0.1.1

- **CI:** the release commit `986a882` (merge of PR #15): all 11 jobs of `tests.yml` passed.
- **PyPI release:** GitHub release `v0.1.1` at `986a882`, published by Ted at 2026-11-10 01:21:41 UTC (19:21 on 9 Nov in Oklahoma City). Publish run 42735239825: the build job (tag check, `twine check --strict`, the suite against the built wheel) passed at 01:22 UTC. The `pypi` job, approved by Ted, uploaded at 01:26 UTC. https://pypi.org/project/ndplex/0.1.1/
- **Files on PyPI:** `ndplex-0.1.1-py3-none-any.whl` (sha256 `6ca0e84e1aac0e35aa2249642f4ad8a297fab1d9bb16a11438796721c52b108a`) and `ndplex-0.1.1.tar.gz` (sha256 `f432cb126893cecb451b43660e3650e65c4893aa3f7e57bda5f4bba4160b013b`). Both carry PyPI provenance attestations naming publisher GitHub `tedteske/ndplex`, workflow `publish.yml`. PyPI lists `Requires-Python >=3.10`, `numpy>=1.23.5` and license MIT; versions 0.1.0 and 0.1.1, latest 0.1.1.
- **Check after release** (*Run*, Linux, 10 Nov UTC): both files downloaded from PyPI match their published sha256. `ndplex==0.1.1` from PyPI, installed into clean environments with no package cache, gave 0.1.1 from `site-packages` on Python 3.13.18 with NumPy 2.5.4 and on Python 3.10.20 with NumPy 1.23.5. On both: the `ImportError` names the examples notebook, and `oeis` identifies itself as `ndplex/0.1.1`. The sdist's suite, run against each install, gave 193 passed, 2 skipped (matplotlib not installed; the original notebook, not in the sdist), including the new release-metadata test. The examples notebook, run against 0.1.1 from PyPI, prints `ndplex 0.1.1`, and its 133 offline cells match the original (`tests/notebook_check.py`).
- **Zenodo:** version 0.1.1 is [10.5281/zenodo.24095480](https://doi.org/10.5281/zenodo.24095480) (as given by Ted from the Zenodo record; Zenodo and doi.org cannot be reached from here, so it was not resolved here). It is in `CITATION.cff` (`identifiers`) and the README's Citing section. The concept DOI, 10.5281/zenodo.24054477, now resolves to 0.1.1 (*Argued*, from how Zenodo concept DOIs work).
- **Date:** `date-released` in `CITATION.cff` and the CHANGELOG heading are 2026-11-10, the UTC date in the GitHub, PyPI and Zenodo records. The release PR had 2026-11-09, Ted's local date, so the 0.1.1 sdist on PyPI carries that date in its CHANGELOG; only this record PR changes it.
