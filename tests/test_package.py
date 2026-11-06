"""
Package-level checks (Phase 2): the public names, lazy loading of oeis, the
private module names, and the plotting functions that left the package.
"""
import importlib
import subprocess
import sys

import pytest

from _impl import IMPORT_IN_SUBPROCESS, impl, ndplex, oeis


def test_public_names():
    assert impl.ndplex is ndplex
    assert callable(oeis) and oeis.__name__ == "oeis"
    assert set(impl.__all__) == {"ndplex", "oeis", "__version__"}
    assert {"ndplex", "oeis", "__version__"} <= set(dir(impl))


def test_from_import_keeps_notebook_calls_working():
    ns = {}
    exec("from ndplex import ndplex, oeis", ns)
    assert ns["ndplex"] is ndplex and ns["oeis"] is oeis


def test_oeis_function_is_not_shadowed_by_a_module():
    """The implementation module is private (_oeis), so importing it cannot
    replace the package attribute `oeis` (the function) with a module."""
    importlib.import_module("ndplex._oeis")
    assert impl.oeis is oeis and callable(impl.oeis)
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("ndplex.oeis")


def test_oeis_is_loaded_on_first_use():
    out = subprocess.run(
        [sys.executable, "-c", IMPORT_IN_SUBPROCESS
         + "a = 'ndplex._oeis' in sys.modules\n"
           "from ndplex import oeis\n"
           "print(a, 'ndplex._oeis' in sys.modules)"],
        capture_output=True, text=True, check=True).stdout.strip()
    assert out == "False True"


@pytest.mark.parametrize("name", ["plot_ndplex", "diag_as_hist"])
def test_plotting_functions_left_the_package(name):
    """Decision (Phase 2): plotting is left to the user. The old names fail
    with a message pointing to the examples notebook."""
    with pytest.raises(ImportError, match="examples notebook"):
        exec(f"from ndplex import {name}", {})


def test_unknown_attribute():
    with pytest.raises(AttributeError):
        impl.no_such_name


def test_version_string():
    parts = impl.__version__.split(".")
    assert parts[:3] == ["0", "1", "0"]
