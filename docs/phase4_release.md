# ndplex — Phase 4: Packaging and release

**Status:** PR #11 merged (`ea2f5fc`). The TestPyPI dry run of 0.1.0 (7 Nov 2026) found P4: oeis.org refused every `oeis` request. The fix (C14, PR #12) passed the TestPyPI check as 0.1.0.dev1 in Colab on 8 Nov 2026, including the live OEIS lookups; the version is back to 0.1.0. Nothing is on PyPI. §8 is filled in after the release.

**Carried over from Phase 3** (PR #10, merged as `34ced3e`): `tests.yml` (11 jobs, all passing), `checks.yml` (mutation and differential checks, run by hand), `docs/phase3_ci.md` (findings P1–P3, change C12), the suite (191 passed, 1 skipped; 192 with matplotlib), and the to-do lists in `docs/phase2_package.md` §9 and `docs/phase3_ci.md` §8.

**Epistemic labels**, as before. *Run* = observed by running the code here (Linux x86_64); true for what was run, not a guarantee beyond it. *Argued* = reasoned, not tested. *Not checked* = could not be run here.

---

## 1. Decisions

- **Name `ndplex`.** On 6 Nov 2026 pypi.org returned 404 for `ndplex` and `ndplex-array` (*Run*, JSON API and simple index). TestPyPI cannot be reached from this environment (*Not checked*); the dry run will show it.
- **Version 0.1.0.** 0.x signals that the API may still change.
- **Zenodo before 0.1.0** (Ted, this phase), so that 0.1.0 gets a version DOI. Zenodo must be switched on before the GitHub release is published.
- **`CITATION.cff` in this phase** (Ted). It ships in 0.1.0 without a DOI; the post-release PR adds the concept DOI, the 0.1.0 version DOI and `date-released`, as in bounded-lognorm. It lists Green (2015) under `references`, as Ted asked in Phase 2 (§9 there).
- **The README is the package's documentation.** It replaces the copied docstrings with a short guide whose examples run as tests (`tests/test_readme.py`), so the PyPI page cannot drift from the package. It cites Green (2015) as a general source. Its links are absolute, since PyPI does not resolve relative links.
- **The plotting `ImportError` points to the repository** (C13 below), because `notebooks/ndplex_examples.ipynb`, which it named, does not exist until Phase 5.

## 2. Changes from Phase 3, with migration notes

- **C13. The message of the `ImportError` for `plot_ndplex` and `diag_as_hist`.** It named `notebooks/ndplex_examples.ipynb`; it now names `ndplex_array.ipynb` and https://github.com/tedteske/ndplex. The exception type and when it is raised are unchanged. *Migration:* none, unless code matched the old message text. Phase 5 can point it at the examples notebook once that exists.
- **C14. `oeis` sends `User-Agent: ndplex/<version> (+https://github.com/tedteske/ndplex)`** instead of Python's default `Python-urllib/3.x` (P4). Nothing else about the request, the parsing or the output changed. *Migration:* none. Before C14, `oeis` printed `lookup failed (HTTP Error 403: Forbidden)` on every row (and with `quiet=True` raised `HTTPError`) wherever oeis.org applies this rule; after it, lookups work. The notebook's own `oeis`, which uses `requests` (header `python-requests/2.x`), may be refused the same way (*Not checked*).

No other behaviour changed: `src/ndplex/_core.py` and `src/ndplex/_oeis.py` are untouched, and `__init__.py` changed only in `__version__` and this message.

### P4. oeis.org refuses Python's default User-Agent

*Found* in the TestPyPI check in Colab (7 Nov 2026, Python 3.13.18, NumPy 2.4.6): every `oeis` request got HTTP 403. *Diagnosed* by `ndplex_oeis_403_diagnostic.ipynb`, run by Ted in Colab the same day: oeis.org is served through Cloudflare, which answered 403 with body `error code: 1010` to all four URLs tried (search as text, search as JSON, home page, a sequence page) with Python's default header, and 200 with the expected content to all four with either a header naming ndplex or a browser-like one. Cloudflare's error 1010 is a refusal based on the client's signature. So the cause is the header, not Colab's network (*Run*, in Colab; true for that network on that day).

The search answer in text format is unchanged in what `oeis` reads: it starts with the greeting line and has `%I`/`%S` lines for A000217; the `%N` line was beyond the 200 characters the diagnostic printed (*Run*, partially). The 0.1.0.dev1 Colab check then ran the full lookups (§7).

ndplex names itself rather than imitating a browser: it is honest, and it lets OEIS contact or limit ndplex specifically. If OEIS later refuses that header too, the fix is theirs to grant or refuse, not ours to get around.

## 3. Files

- `src/ndplex/__init__.py`: `__version__ = "0.1.0"`; C13. (In the C14 PR, `0.1.0.dev1` for the TestPyPI test, set back to `0.1.0` before merging.)
- `src/ndplex/_oeis.py` (C14 PR): the User-Agent. `tests/test_oeis.py`: the network-call test checks the header.
- `README.md`: rewritten (§1).
- `CHANGELOG.md`: the 0.1.0 entry (dated 6 Nov 2026; the post-release PR corrects the date if the release is later).
- `CITATION.cff`: new. Valid against CFF schema 1.2.0, and cffconvert turns it into Zenodo metadata without error (*Run*, cffconvert 2.0). Zenodo's own import is *Not checked* until the release.
- `pyproject.toml`: `CITATION.cff` added to the sdist.
- `.github/workflows/publish.yml`: new (§4).
- `tests/test_readme.py`: new, 2 tests. `tests/test_package.py`: the plotting test matches C13's message.
- `ATTRIBUTION.md`: Phase 4 under tier B.

## 4. `publish.yml`

As in bounded-lognorm: Trusted Publishing (OIDC), no stored tokens. Running the workflow by hand publishes to TestPyPI; publishing a GitHub release tagged `v<version>` publishes to PyPI. Both paths build once, run `twine check --strict` and the full suite against the built wheel, then upload that same artifact. The `pypi` job waits for Ted's approval (a GitHub environment rule, §5).

Differences from bounded-lognorm's file, all in the build job:

- The suite runs in a fresh virtual environment with only the wheel and the `test` dependency group installed, and the job fails unless `ndplex` is imported from `site-packages`, so the tests cannot pick up the source tree.
- The tag check also fails if `__version__` cannot be read (an empty version would otherwise compare as `v`).

Replayed locally (*Run*): the build; `twine check --strict` (both files pass); the tag check (accepts `v0.1.0`, rejects `v0.1.1`); the fresh-venv install of the wheel, the `site-packages` check and the suite (193 passed, 1 skipped for matplotlib). The upload steps and the OIDC exchange are *Not checked* until the dry run.

## 5. One-time setup (Ted)

1. **TestPyPI** (https://test.pypi.org, log in) → Your account → Publishing → *Add a new pending publisher* → GitHub: project name `ndplex`, owner `tedteske`, repository `ndplex`, workflow `publish.yml`, environment `testpypi`.
2. **PyPI** (https://pypi.org) → the same form, with environment `pypi`.
3. **GitHub environments** (github.com/tedteske/ndplex → Settings → Environments → New environment):
    - `testpypi`: no protection rules.
    - `pypi`: tick *Required reviewers*, add `tedteske`, and leave *Prevent self-review* unticked. Optionally, under *Deployment branches and tags*, allow only tags matching `v*`.
4. **Zenodo** (https://zenodo.org, log in with GitHub) → your name → GitHub → find `tedteske/ndplex` → switch it **On**. (If it is not listed, press *Sync now*.) This must be done before step 3 of §6.

## 6. Releasing 0.1.0

1. Review and merge this PR.
2. **TestPyPI dry run:** Actions → publish → Run workflow. Then run `ndplex_testpypi_check.ipynb` in Colab and send back its output. A version can be uploaded to TestPyPI only once (TestPyPI and PyPI are separate, so 0.1.0 stays free on PyPI). 0.1.0 was run from `master` on 7 Nov 2026 and found P4; the C14 fix is run from its PR branch as `0.1.0.dev1`, then the branch is set back to `0.1.0` and merged.
3. **Release:** Releases → Draft a new release → *Choose a tag* → type `v0.1.0` → *Create new tag on publish*, target `master`; title `ndplex 0.1.0`; paste the release notes; tick *Set as the latest release*; *Publish release*.
4. **Approve:** Actions → the publish run → *Review deployments* → tick `pypi` → *Approve and deploy*.
5. Tell Claude. Claude checks a clean install from PyPI and opens the PR that records the release, the DOIs and the date.

**Release notes** (to paste in step 3):

> First release of ndplex, the n-Dimensional m-Plex array (Ted Teske, 2019–2024), as a Python package: `pip install ndplex`. It needs only NumPy (1.23.5 or later) and Python 3.10 or later.
>
> The package keeps the notebook's results except where a change is documented. The main changes: importing it no longer restyles plots or silences warnings; plotting (`plot_ndplex`, `diag_as_hist`) stays in the notebook; integer overflow is reported with a warning, and `dtype=object` is exact; `arg_locs` outside the array read 0; `diag` ends where its moves leave the array; `as_tri` layers are justified left in every dimension; `oeis` uses https, identifies itself to oeis.org (which now refuses Python's default identification) and reports failed lookups. Details and migration notes: [CHANGELOG.md](https://github.com/tedteske/ndplex/blob/master/CHANGELOG.md) and [docs/](https://github.com/tedteske/ndplex/tree/master/docs).
>
> Tested on Linux, macOS and Windows, Python 3.10–3.15, NumPy 1.23.5 to current. The packaging, tests and audit were developed with assistance from Claude (Anthropic).

Zenodo archives the release when it is published (step 3), whether or not the PyPI upload succeeds. The tag check and the suite run before the approval point, so a failure there stops the upload but not the Zenodo record (*Argued*).

## 7. Checks run in this phase (*Run*)

- Suite, Python 3.13.18, NumPy 2.5.4, matplotlib: 194 passed (192 before, plus the 2 README tests).
- Suite, Python 3.10.20, NumPy 1.23.5: 193 passed, 1 skipped (matplotlib not installed).
- README test, mutation-tested by hand: a wrong Fibonacci output and the blocks renamed so that none is found each fail it.
- Sdist: contains the tests, docs, README, CHANGELOG, ATTRIBUTION, CITATION.cff and LICENSE; its tests run against the installed wheel give 192 passed, 2 skipped (matplotlib; the notebook, which is not in the sdist). Wheel: the three modules and the license.
- Differential check against the notebook's code: all equal, 4822 comparisons.
- Mutation check (`--expect tests/mutation_equivalent.txt`): 479 mutants, 468 killed, 11 survived, exactly the 11 listed as equivalent.
- The Colab check notebook's Python cells, run locally against the wheel: cells 2, 3 and 6 print PASS; cells 4 and 5 report the failed lookups, because oeis.org is not reachable from here.
- **TestPyPI dry run of 0.1.0** (7 Nov 2026, run `42384434504`): build and wheel tests passed, the TestPyPI upload passed, PyPI skipped. In Colab (Python 3.13.18, NumPy 2.4.6): installed from TestPyPI; all 9 array checks passed; `oeis` refused (P4). Two mistakes of the check notebook, not the package: cell 2 looked for `site-packages`, but Colab installs to `dist-packages`; cell 7 built the sdist to download it, which needs hatchling from TestPyPI. Both fixed in the dev1 check notebook.
- **C14:** suite 194 passed (Python 3.13); on a local HTTP server, the request carries `User-Agent: ndplex/0.1.0.dev1 (+https://github.com/tedteske/ndplex)`; suite on Python 3.10 with NumPy 1.23.5: 193 passed, 1 skipped (matplotlib); mutation check: 482 mutants, 471 killed, 11 survived, exactly the 11 listed as equivalent (the 3 new mutants of the User-Agent code are killed); the dev1 check notebook's cells 2, 3, 6 and 7 (on the local sdist: 192 passed, 2 skipped) print PASS locally.
- **TestPyPI check of 0.1.0.dev1** (8 Nov 2026, Colab, Python 3.13.18, NumPy 2.4.6), all cells PASS: installed from TestPyPI to `dist-packages`, warning filters unchanged; the 9 array checks; `oeis(ndplex(5))` against the live oeis.org found A000012, A000027, A000217, A000292 and A000332, the notebook's results, and `quiet=True` returned the same; failed lookups reported per row; the sdist's suite against the installed wheel, 193 passed, 1 skipped (the notebook, not in the sdist). The sequence names printed are OEIS's current ones and are longer than those in the notebook's saved outputs; names can change, A-numbers are what the check compares.

## 8. Release record: 0.1.0

*Filled in after the release.*

## 9. Not checked

- **PyPI upload, the `pypi` approval gate:** the release.
- **The README as PyPI renders it:** `twine check` passes, but the page itself is seen first on TestPyPI.

## 10. For Phase 5

- Unchanged from `docs/phase2_package.md` §9 and `docs/phase3_ci.md` §8.
- Point the plotting `ImportError` (C13) and the README's *Plotting* section at `notebooks/ndplex_examples.ipynb` once it exists.
- The link audit of the notebook's references (ATTRIBUTION.md).
