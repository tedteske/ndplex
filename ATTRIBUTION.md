## Attribution & References

### Provenance

This repository contains work of three kinds. They are kept apart so that credit, and responsibility for errors, lands in the right place.

**A. Original work: Ted Teske (2019–2024), sole author**

- The n-Dimensional m-Plex ("ndplex") array: a generic Pascal's array of any dimension, as an `np.ndarray` subclass with user-defined edges, node-generating function (`func`) and argument locations (`arg_locs`, including the `None`-means-on-the-edge convention).
- `diag`, the general line or cross-section through the array (loc, one or more moves, optional sums), and `as_tri`, the array as a triangle, tetrahedron or n-simplex.
- `oeis` (row-by-row OEIS lookup), `diag_as_hist` (weighted histograms with a normal overlay) and `plot_ndplex` (the array or triangle with highlighted diagonals).
- All of `ndplex_array.ipynb`: the examples and the observations in them, including the simplex/duplex/triplex triangles, the binomial-to-normal histograms, Fibonacci and Narayana's cows from steep diagonals, the slope table, the moving-cost and rental-rate model, and the explorations with primes.

**B. Collaborative work: Ted Teske with Claude (Anthropic), 2026**

- *Phase 1 audit* (`docs/phase1_audit.md`): running the notebook against current libraries; the findings on import side effects, the ndarray subclass, integer overflow (where it starts, why residues modulo powers of 2 survive it, and that part of the Fibonacci-mod-7 heatmap is overflow), arg_locs that wrap around the array, diag trimming genuine zeros, and oeis hiding network errors; the proposed 0.1.0 API.
- *Phase 1 regression suite* (`tests/`): the notebook's printed results pinned as tests, the property checks (binomial, multinomial, Lucas's theorem, digital roots), the known-issue tests, the offline OEIS stub and primes sieve, and the mutation check (`tests/mutation_check.py`).
- *Phase 2 package* (`src/ndplex`, `pyproject.toml`, `docs/phase2_package.md`): the package layout and lazy loading of `oeis`; the fixes for the Phase 1 findings (no import side effects, a single overflow warning naming the first overflowed node, exact `dtype=object` sums, derived arrays that keep working and pickle, zero padding for `arg_locs` outside the array, `diag` ending by geometry rather than at the first trailing zeros, argument checks, and `oeis` over https with failures reported and a `quiet` mode). The class's design, its node-generation loop, the edge-filling rotation, the `diag` move arithmetic and the `as_tri` move pattern are Ted's, kept from the notebook (tier A).
- *Phase 2 tests*: the suite moved to the package, the known-issue tests rewritten to the fixed behaviour, the new package, overflow, pickling and `oeis` tests, the differential check against the notebook code, and the mutation check adapted to the package.

**C. Third-party work, cited below**

Attribution suggestion, not a rule: the usual convention in published work is that an AI system is not listed as an author, since authorship carries accountability an AI cannot hold. The conventional form is to claim the work as your own and acknowledge AI assistance, e.g. *"The test suite and audit were developed with assistance from Claude (Anthropic)."*

### References

**General source.** Ted cites Thomas M. Green's *The Simplex, Duplex and Pascal's Triangles* (2015; reference 10 below) as a general source for ndplex. The book covers Pascal's triangle and its relatives, simplexes, duplexes and higher-dimensional extensions, and recurrent sequences such as Fibonacci.

**Code adapted in the notebook's library cell (not in the package)**

1. `trim_trailing_zeros` (inside `diag`) is adapted from an answer to "Trim trailing zeros of a numpy array along each axis", Stack Overflow question 55917328. https://stackoverflow.com/questions/55917328
2. The query inside `oeis` is adapted from Andrew Walker's `oeis` package. https://github.com/AndrewWalker/oeis — its `setup.py` declares a BSD license; the repository has no LICENSE file (checked November 2026).

*Both are kept here as history. The package does not contain either (decision D9): `diag` now ends where its moves leave the array (`_trim_outside` in `src/ndplex/_core.py`, written from scratch for the change in behaviour) and `oeis`'s request is written from scratch with the standard library. The notebook (`ndplex_array.ipynb`) still contains the originals.*

**Code and data used only in the notebook's examples**

3. `sum_digits`, from Andreas K.'s answer to Stack Overflow question 48817036. https://stackoverflow.com/questions/48817036
4. `primesfrom2to`, from an answer to Stack Overflow question 2068372. https://stackoverflow.com/questions/2068372
5. The first 1000 primes, downloaded from a GitHub gist by cblanc. https://gist.github.com/cblanc/46ebbba6f42f61e60666

**Mathematics and sources cited in the notebook**

6. The On-Line Encyclopedia of Integer Sequences (OEIS). https://oeis.org — the source of the sequence names `oeis()` prints; its text output format is described at https://oeis.org/eishelp1.html.
7. Pascal's triangle and the bell curve. AMS Feature Column. http://www.ams.org/publicoutreach/feature-column/fcarc-normal
8. Pascal's triangle modulo n (Sierpinski's gasket). http://orion.math.iastate.edu/reu/oldREU/modupasc.htm
9. Hypercube; Simplex. Wikipedia. https://en.wikipedia.org/wiki/Hypercube, https://en.wikipedia.org/wiki/Simplex
10. Green, Thomas M. *The Simplex, Duplex and Pascal's Triangles: Relatives of Pascal's Triangle, with Excursions Into Hyperspace*. CreateSpace Independent Publishing Platform, 2015. 176 pp. ISBN 9781514677094. https://books.google.com/books/about/The_Simplex_Duplex_and_Pascal_s_Triangle.html?id=P0cDswEACAAJ (also cited in the notebook, via https://www.amazon.com/Simplex-Duplex-Pascals-Triangles-Excursions/dp/1514677091). **A general source for the project** (see the note above), not only for the notebook section that cites it.
11. Narayana's cows sequence, OEIS A000930 (https://oeis.org/A000930), and the paper linked from the notebook (JIM 96 proceedings). http://jim.afim-asso.org/jim96/actes/Allouche.ps

**Used in the Phase 1 tests**

12. Lucas's theorem (a binomial coefficient modulo a prime, from base-p digits); for p = 2 it gives: C(i + j, i) is odd exactly when i AND j = 0. https://en.wikipedia.org/wiki/Lucas%27s_theorem
13. The multinomial theorem: the nodes of layer r of the d-dimensional default ndplex sum to d^r.

*Links in the notebook have not yet been checked; a link audit is planned with the examples notebook (Phase 5).*
