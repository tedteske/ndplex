"""
The implementation under test, loaded in one place.

Phase 1 tests the notebook's original code (tests/ndplex_original.py).
Phase 2 will point this module at the package (`from ndplex import ...`);
the regression tests themselves should not need to change, except where a
documented behaviour change says so.

NDPLEX_IMPL_PATH, if set, loads another file instead. The mutation check
(tests/mutation_check.py) uses it to run the suite against mutated copies.
"""
import importlib.util
import os
import pathlib
import sys
import warnings

import matplotlib

matplotlib.use("Agg")  # no display in tests; must precede pyplot import

_DEFAULT = pathlib.Path(__file__).with_name("ndplex_original.py")
PATH = pathlib.Path(os.environ.get("NDPLEX_IMPL_PATH", _DEFAULT))


def _load(path):
    spec = importlib.util.spec_from_file_location("ndplex_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod  # so instances can be pickled
    # The original calls warnings.simplefilter('ignore') at import time
    # (audit finding F1). Undo it so the test process keeps its own filters.
    with warnings.catch_warnings():
        spec.loader.exec_module(mod)
    return mod


impl = _load(PATH)

ndplex = impl.ndplex
oeis = impl.oeis
diag_as_hist = impl.diag_as_hist
plot_ndplex = impl.plot_ndplex
