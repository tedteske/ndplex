"""
The implementation under test, loaded in one place.

Phase 1 tested the notebook's original code (tests/ndplex_original.py, kept
as the record of what the notebook did). From Phase 2 the suite tests the
package as installed (`pip install -e .`, or a built wheel), so a packaging
mistake fails the tests instead of being hidden by the source tree.

NDPLEX_IMPL_PATH, if set, is a directory containing an `ndplex` package to
test instead. The mutation check (tests/mutation_check.py) uses it to run
the suite against mutated copies of src/ndplex.
"""
import os
import sys

PATH = os.environ.get("NDPLEX_IMPL_PATH")
if PATH:
    sys.path.insert(0, PATH)

try:
    import ndplex as impl
except ImportError as err:  # pragma: no cover
    raise ImportError("install the package first: pip install -e .") from err

ndplex = impl.ndplex
oeis = impl.oeis
oeis_module = sys.modules["ndplex._oeis"]

# Code that imports the same package in a fresh Python process.
IMPORT_IN_SUBPROCESS = "import sys\n" + (
    (f"import sys; sys.path.insert(0, {PATH!r})\n" if PATH else "")
    + "import ndplex\n")
