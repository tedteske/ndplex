"""tests/ndplex_original.py must stay a verbatim copy of the notebook cell."""
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "ndplex_array.ipynb"
COPY = pathlib.Path(__file__).with_name("ndplex_original.py")


def test_original_copy_matches_notebook():
    if not NOTEBOOK.exists():
        pytest.skip("notebook not present")
    cells = json.loads(NOTEBOOK.read_text())["cells"]
    lib = [''.join(c["source"]) for c in cells
           if c["cell_type"] == "code" and "class ndplex(np.ndarray)" in ''.join(c["source"])]
    if not lib:
        pytest.skip("notebook no longer contains the library cell")
    body = COPY.read_text().split("# END HEADER\n", 1)[1].split("\n", 1)[1]
    assert body.rstrip("\n") == lib[0].rstrip("\n")
