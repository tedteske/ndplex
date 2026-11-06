"""
Differential check: the package against the notebook's original code.

Compares ndplex (installed package) with tests/ndplex_original.py on inputs
where Phase 2 says nothing should change: construction with edges, func and
arg_locs that stay inside the array, in 1-4 dimensions; random diag calls
(one or two moves) on arrays with no genuine zeros; and as_tri for every
start/end; and a loc that fixes only some axes, with the default move.
Calls on which the original raises (all-padding lines, audit
finding N2) are skipped; those are covered by the regression suite.

    pip install -e . scipy seaborn requests matplotlib
    python tests/differential_check.py

The original needs its own imports (scipy, seaborn, requests, matplotlib),
so this is not part of the pytest run. Result in Phase 2 (6 Nov 2026):
all equal, 3527 comparisons.
"""
import importlib.util
import itertools
import pathlib
import random
import warnings

import numpy as np

ORIGINAL = pathlib.Path(__file__).with_name("ndplex_original.py")


def load_original():
    spec = importlib.util.spec_from_file_location("ndplex_original", ORIGINAL)
    mod = importlib.util.module_from_spec(spec)
    with warnings.catch_warnings():  # the original silences all warnings
        spec.loader.exec_module(mod)
    return mod


def same(a, b):
    a, b = np.asarray(a), np.asarray(b)
    return a.shape == b.shape and (a == b).all()


def main(seed=1):
    orig = load_original()
    from ndplex import ndplex as new
    warnings.simplefilter("ignore")  # overflow warnings are expected
    rng = random.Random(seed)
    n_checks = 0

    # 1. Construction.
    cases = []
    for ndim in (1, 2, 3, 4):
        for n in (1, 2, 3, 5, 7):
            if ndim == 4 and n > 5:
                continue
            cases.append(dict(nrows=n, edges=ndim))
            cases.append(dict(nrows=n, edges=tuple(rng.randint(1, 5)
                                                   for _ in range(ndim))))
    for n in (3, 6, 9):
        cases += [
            dict(nrows=n, edges=(list(range(1, n + 1)), 2)),
            dict(nrows=n, edges=(1, 1), func=lambda x: x[0] * 2 + x[1]),
            dict(nrows=n, edges=(1, 1), arg_locs=[[-1, 0], [0, -1], [-1, -1]]),
            dict(nrows=n, edges=(1, 1), arg_locs=[[None, 0], [0, None]],
                 func=lambda x: x[0] + x[1]),
            dict(nrows=n, edges=(2, 3), dtype=float, func=lambda x: sum(x) / 2),
            dict(nrows=n, edges=(1, 1), dtype=object),
        ]
    for kw in cases:
        assert same(orig.ndplex(**kw), new(**kw)), kw
        n_checks += 1

    # 2. diag and as_tri on arrays with no genuine zeros.
    for d in (2, 3):
        for n in (1, 2, 4, 6, 9):
            p, o = new(n, edges=d), orig.ndplex(n, edges=d)
            combos = [((), ())]
            for _ in range(150):
                loc = tuple(rng.randint(0, n - 1) for _ in range(d))
                nm = rng.randint(1, 2)
                move = [tuple(rng.randint(-3, 3) for _ in range(d))
                        for _ in range(nm)]
                if any(all(v == 0 for v in m) for m in move):
                    continue
                combos.append((loc, move if nm > 1 else move[0]))
            for loc, move in combos:
                for sum_axis in (None, 0):
                    try:
                        want = o.diag(loc=loc, move=move, sum_axis=sum_axis)
                    except Exception:
                        continue
                    got = p.diag(loc=loc, move=move, sum_axis=sum_axis)
                    assert same(want, got), (n, d, loc, move, sum_axis)
                    n_checks += 1
            # A loc that fixes only some axes (sub-arrays), default move.
            # (Not for n = 1: there the notebook's result kept a squeezed
            # padding axis; the package gives 0-d, as for a full loc.)
            for loc in [] if n == 1 else [(i,) for i in range(n)] + (
                    [(i, j) for i in range(n) for j in range(n)] if d == 3 else []):
                assert same(o.diag(loc=loc), p.diag(loc=loc)), (n, d, loc)
                n_checks += 1
            if n > 1:
                for s, e in itertools.combinations_with_replacement(range(n), 2):
                    for sums in (False, True):
                        assert same(o.as_tri(s, e, sums), p.as_tri(s, e, sums))
                        n_checks += 1
    print(f"all equal; {n_checks} comparisons")


if __name__ == "__main__":
    main()
