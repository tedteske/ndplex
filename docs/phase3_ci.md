# ndplex — Phase 3: Tests and CI

**Status:** done, pending review (PR #10). CI runs on every pull request and push to master. One behaviour change (C12), found by testing on NumPy 1.23.5. Nothing is released; the version is still `0.1.0.dev0`.

**Carried over from Phase 2** (PR #9, merged): the `src/ndplex` package (NumPy only), `docs/phase2_package.md` (decisions D1–D10, changes C1–C11), the suite (170 tests), `tests/differential_check.py` and `tests/mutation_check.py` (450 mutants, 440 killed, 10 equivalent), `CHANGELOG.md` and `ATTRIBUTION.md`.

**Epistemic labels**, as before. *Run* = observed by running the code; true for what was run, not a guarantee beyond it. *CI* = observed in the GitHub Actions run on PR #10. *Argued* = reasoned from the code, not tested exhaustively. *Not checked* = could not be run.

**Confidence in the platform results:** they show the suite passes on the CI runners' current images (macOS arm64, Windows x86-64); they are not proof for other machines.

**Local environments** (*Run*, Linux x86_64): Python 3.10.20, 3.11.18, 3.12.3, 3.13.18, 3.14.6 and 3.15.0b4 with the latest NumPy each supports (2.2.6 on 3.10, 2.4.6 on 3.11, 2.5.4 on the rest), and Python 3.10.20 with NumPy 1.23.5.

---

## 1. CI (`.github/workflows/tests.yml`)

As bounded-lognorm's `tests.yml`, adapted:

- **Test jobs** (each installs the package, not editable, with the `test` dependency group, then runs `python -m pytest` from the repository root):
    - Linux, Python 3.10–3.15, latest dependencies (pre-release Python allowed, for 3.15).
    - Linux, Python 3.13, latest dependencies, plus matplotlib. `NDPLEX_REQUIRE_MATPLOTLIB=1` is set there, so the import-style test (F1) fails instead of skipping if matplotlib is missing.
    - Linux, Python 3.10, NumPy 1.23.5 (the declared minimum, pinned by a constraints file).
    - macOS, Python 3.13, latest dependencies.
    - Windows, Python 3.13, latest dependencies.
    - **Windows, Python 3.10, NumPy 1.23.5.** Not in bounded-lognorm's matrix and not in the Phase 3 brief. Added because it is the one configuration where NumPy's default integer (`dtype=int`) is int32 (finding P2); NumPy 2 made it int64 on Windows too. One extra job; drop it if you prefer the brief's single Windows run.
- **Build job:** builds the sdist and wheel, runs `twine check --strict`, installs the wheel in a clean venv and imports it outside the source tree, and uploads `dist/` as an artifact. The same steps pass locally (*Run*).
- **Triggers:** pull requests, pushes to master, and by hand (`workflow_dispatch`). Read-only permissions; a newer run on the same branch cancels the older one.
- **Report header:** every pytest run now prints the ndplex path, NumPy version, NumPy's default int, OS and machine, so a CI log shows which platform facts a result rests on.

**Result:** all 11 jobs pass (§5).

---

## 2. Findings

**P1. Overflow was not reported for narrow integer dtypes on NumPy < 2** (*Run*; fixed, C12).

- `ndplex(40, dtype=np.int32)` on NumPy 1.23.5 (Linux) gives 747 wrong (wrapped) nodes and no warning. On NumPy 2.5.4 the values are identical and the warning is issued. The same holds for int8, int16, uint8, uint16 and uint32. int64 was reported on both.
- Cause (*Run*, then *Argued*): the default `func=sum` starts from the Python int 0. On NumPy < 2, `0 + np.int32(x)` is promoted to the platform's default int (int64 on Linux and macOS), so the sum never overflows inside NumPy's arithmetic and `np.errstate` sees nothing; the out-of-range int64 is then wrapped silently when stored in the int32 array. NumPy 2 (NEP 50) keeps the total as int32, so the overflow is signalled.
- A related difference: a `func` returning an integer too large for the dtype (e.g. `np.int64(x[0]) + np.int64(x[1])` into an int8 array, or a Python int) was wrapped silently on NumPy 1.23.5 and raised `OverflowError` on NumPy 2.2–2.5 (*Run*). Python ints beyond the int64 range raised `OverflowError` on both.
- On Windows with NumPy < 2 the default int is int32, so int32 overflow from `sum` was reported there but int8 and int16 were not (*Argued* from the cause above; the Windows/NumPy 1.23.5 CI job now runs the tests).

**P2. `dtype=int` is NumPy's default integer, which depends on the platform** (*Run* on Linux; documented, no change).

- int64 on Linux and macOS, and on Windows with NumPy ≥ 2; int32 on Windows with NumPy < 2. The default dtype stays `np.int64` everywhere (C7, Phase 2). `test_dtype_int_is_numpys_default_int` checks that `dtype=int` gives `np.dtype(int)` and that its overflow is reported, whatever that type is.

**P3. A Phase 1 test assumed the platform's default int** (*CI*; test fixed, no package change).

- `test_default_rectangle_values` asserted `dtype == np.dtype(int)`, the notebook's default. Phase 2 made the default `np.int64` everywhere (C7), and the test kept passing because the two are equal except on Windows with NumPy < 2. The Windows/NumPy 1.23.5 job failed on it (int64 ≠ int32): the package was right and the test was stale. The test now asserts `np.int64`.
- The same job confirms C7 where it matters: `test_default_dtype_is_int64` passed there, with NumPy's default int reported as int32 (*CI*).

**Other platform checks** (*Argued*, confirmed by CI where it ran):

- Text files are read as UTF-8 explicitly (`tests/test_original_copy.py`, `tests/mutation_check.py`). The files involved are ASCII today, so this changes nothing on Linux; it guards against Windows' locale encoding if a non-ASCII character is ever added.
- Subprocess tests (import side effects, lazy `oeis`) use `sys.executable` and compare stripped output, so Windows line endings do not matter.
- The package has no float types whose size differs by platform (no `longdouble`), no file or path handling, and no compiled code.

---

## 3. Changes from Phase 2, with migration notes

**C12. Overflow is reported for every integer dtype, the same way on every NumPy version** (P1).

- During construction, each integer `func` returns (a Python int or NumPy integer of a type other than the array's) is checked against the dtype's range. An out-of-range value is wrapped modulo 2^bits (two's complement, as NumPy wraps) before it is stored, and the first such node is named in the one overflow warning, as for overflow inside `func` (C3).
- Results (*Run*): the six dtypes above now warn on NumPy 1.23.5, naming the same node as NumPy 2; values are unchanged on both. The default int64 array is unaffected: values of the array's own type skip the check.
- This replaces the limit stated in Phase 2's C3 ("a `func` returning a value too large for int64 raises `OverflowError`").
- *Migration:*
    - NumPy < 2 with int8/16/32 or unsigned dtypes: none for results; a warning now appears where values wrap. Silence it as in C3, or use `dtype=object`.
    - NumPy 2, a `func` returning an integer outside the dtype's range, or any NumPy with a Python int beyond int64: construction used to raise `OverflowError`; it now wraps and warns. Code that relied on the exception can turn the warning into an error: `with warnings.catch_warnings(): warnings.simplefilter("error", RuntimeWarning)`.
- *Speed* (*Run*, A/B on the same machine, best of 15): default `ndplex(300)` and `ndplex(40, edges=3)`, no measurable change (within ±5% run-to-run noise). `ndplex(300, dtype=np.int32)` on NumPy 1.23.5 about 15% slower, since every value is checked there.
- *Decision for Ted:* wrapping keeps C12 consistent with D3a (warn, keep NumPy's wrapped values). The alternative is to raise `OverflowError` for out-of-range `func` results on every NumPy version and warn only for overflow inside `func`. It is a few lines either way.

---

## 4. Tests

- **Suite H, `tests/test_platform.py`** (new, 22 tests): overflow for int8 to int64 and uint8 to uint32 (wrapped values, first node, one warning), in 3-D, at the edges of the int8 range (127 and −128 fit; 128 and −129 wrap and warn), Python ints beyond int64, values after the first overflow, no false alarms (values that fit narrow dtypes, truncation of float results, non-integer dtypes), and `dtype=int`.
- **Report header** in `tests/conftest.py` (it imports through `tests/_impl.py`, so it honours `NDPLEX_IMPL_PATH` and reports the mutant under test).
- **`NDPLEX_REQUIRE_MATPLOTLIB`** in the F1 style test. Checked (*Run*): with it set and matplotlib missing, the test fails; with matplotlib installed and a copy of the package that sets `axes.facecolor` on import, the test fails (and so does the numpy-only import test).
- **Totals** (*Run*): 191 passed and 1 skipped without matplotlib; 192 passed with it; on every local environment listed above. On Windows (*CI*) every Suite H test passed in both Windows jobs, including on NumPy 1.23.5, where `dtype=int` is int32.
- **Suite H against the Phase 2 code** (*Run*): 12 of its tests fail on NumPy 1.23.5 and 5 on NumPy 2.5.4, so the suite detects P1 on both.

**Mutation check** (*Run*, 6 Nov 2026, 2 jobs, about 3 minutes): **479 mutants, 468 killed, 11 survived.** The 29 new mutants are in the C12 code; 28 are killed. The survivors are Phase 2's 10 equivalent mutants (§7 of `docs/phase2_package.md`, at shifted line numbers) and one new one:

- `(v - low) % span + low` → `(v + low) % span + low` (*Argued* equivalent: `low` is 0 for unsigned types and −2^(bits−1) for signed ones, so `2·low` is 0 or −2^bits and the two are congruent modulo `span = 2^bits`).

**Differential check** (*Run*): all equal, 4822 comparisons, as in Phase 2. It took about 6 seconds.

---

## 5. CI results

First run (*CI*, commit `66aa9bd`): 10 of 11 jobs passed. Linux 3.10–3.15 (latest NumPy), Linux 3.10 on NumPy 1.23.5, Linux with matplotlib, macOS, Windows 3.13 (NumPy 2.5.4, default int int64) and the build job passed. Windows 3.10 on NumPy 1.23.5 (default int int32) failed one test: P3, fixed in the next commit.

Second run (*CI*, commit `4cbcb8a`): **all 11 jobs passed.** Per job, as the report header shows it:

- Linux x86-64: Python 3.10.22 (NumPy 2.2.6), 3.11.18 (2.4.6), 3.12.16, 3.13.18, 3.14.10 and 3.15.2 (2.5.4): 191 passed, 1 skipped (matplotlib).
- Linux, Python 3.13.18 with matplotlib: 192 passed, nothing skipped.
- Linux, Python 3.10.22, NumPy 1.23.5: 191 passed, 1 skipped.
- macOS arm64, Python 3.13.17, NumPy 2.5.4: 191 passed, 1 skipped.
- Windows AMD64, Python 3.13.17, NumPy 2.5.4 (default int int64): 191 passed, 1 skipped.
- Windows AMD64, Python 3.10.11, NumPy 1.23.5 (default int int32): 191 passed, 1 skipped.
- Build and check: sdist and wheel built, `twine check --strict` passed, the wheel imports from a clean venv.

---

## 6. Differential and mutation checks: CI or on demand?

Both stay on demand for now; this is Ted's decision (see the PR description). Facts for it:

- The mutation check takes about 3 minutes on 2 cores here; a GitHub-hosted Linux runner has 4. The differential check takes seconds but needs scipy, seaborn, requests and matplotlib, because it loads the notebook's original code.
- Neither changes unless `src/ndplex` changes, and both were run for this PR.

---

## 7. Not checked

- **The live OEIS**, as in Phase 2.
- **Colab:** Phase 5.
- **macOS on Intel and Windows on ARM:** the CI runners are macOS ARM and Windows x86-64.

---

## 8. For later phases

- **Phase 4:** as listed in `docs/phase2_package.md` §9, plus the publish workflow (`publish.yml`), whose build job should run this suite against the built wheel.
- **Phase 5:** the examples notebook's overflow cells (C3) will show the C12 warning only where they already overflowed; nothing new is expected there (*Argued*: they use int64).
