"""
README examples (Phase 4): every ```pycon block in README.md is run as a
doctest against the installed package, so the PyPI page cannot drift from
what the package does. Blocks marked ```python (the oeis example, which
needs the network) are not run.
"""
import doctest
import re
from pathlib import Path

import pytest

from _impl import impl

README = Path(__file__).resolve().parents[1] / "README.md"
BLOCK = re.compile(r"^```pycon\n(.*?)^```", re.S | re.M)


def _blocks():
    text = README.read_text(encoding="utf-8")
    return [m.group(1) for m in BLOCK.finditer(text)]


def test_readme_has_examples():
    assert len(_blocks()) >= 8


def test_readme_examples():
    """The blocks run in order in one namespace, as a reader would type them."""
    parser = doctest.DocTestParser()
    runner = doctest.DocTestRunner(optionflags=doctest.ELLIPSIS)
    globs = {"ndplex": impl.ndplex}
    for i, block in enumerate(_blocks()):
        test = parser.get_doctest(block, globs, f"README block {i}",
                                  str(README), 0)
        runner.run(test, clear_globs=False)
        globs = test.globs  # DocTest copies globs; carry names forward
    result = runner.summarize(verbose=False)
    assert result.attempted > 0
    if result.failed:
        pytest.fail(f"{result.failed} README example(s) failed; see output")
