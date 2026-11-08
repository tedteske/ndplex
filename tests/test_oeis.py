"""
Suite E -- oeis(), with the network stubbed out.

The real OEIS is never contacted. A fake replaces the module's single
network call (`ndplex._oeis.urlopen`), records what was asked, and answers
in OEIS's text format (lines tagged %I, %S, %N, ...; see
https://oeis.org/eishelp1.html). What is pinned is the request oeis()
builds, how it parses the answer, what it prints, and (with quiet=True)
what it returns.

Phase 2 changes from the notebook (C8, decision D7; migration notes in
docs/phase2_package.md): the request and the printed links use https
instead of http; failed lookups print "lookup failed (...)" instead of
"no match"; quiet=True returns the results instead of printing. Everything
else printed is unchanged.

Not checked: that today's oeis.org still answers in this format. The fake's
"no results" page is modelled on the format, not captured from the site.
"""
import urllib.parse

import numpy as np
import pytest

from _impl import impl, ndplex, oeis, oeis_module

NAMES = {
    "1,1,1,1,1": "A000012 The simplest sequence of positive numbers: the all 1's sequence.",
    "1,2,3,4,5": "A000027 The positive integers.",
    "1,3,6,10,15": "A000217 Triangular numbers: a(n) = binomial(n+1,2).",
}
GREETING = "# Greetings from The On-Line Encyclopedia of Integer Sequences!\n\n"


class FakeOEIS:
    def __init__(self, body=None, error=None):
        self.calls = []
        self.body, self.error = body, error

    def __call__(self, url, timeout):
        base, _, query = url.partition("?")
        params = dict(urllib.parse.parse_qsl(query))
        self.calls.append((base, params, timeout))
        if self.error is not None:
            raise self.error
        if self.body is not None:
            return self.body
        name = NAMES.get(params["q"])
        if name is None:  # OEIS's "no results" page has no %N line
            return GREETING + "Search: seq:" + params["q"] + "\n\nNo results.\n"
        anum = name.split()[0]
        return (GREETING + f"%I {anum}\n%S {anum} {params['q']}\n%N {name}\n"
                f"%C {anum} A comment line.\n")


@pytest.fixture
def fake(monkeypatch):
    f = FakeOEIS()
    monkeypatch.setattr(oeis_module, "urlopen", f)
    return f


def test_request_format(fake):
    oeis(np.array([1, 2, 3, 4, 5]))
    assert fake.calls == [("https://oeis.org/search",
                           {"q": "1,2,3,4,5", "n": "1", "fmt": "text"}, 10)]


def test_timeout_is_passed_through(fake):
    oeis(np.array([1, 2, 3, 4, 5]), timeout=2.5)
    assert fake.calls[0][2] == 2.5


def test_1d_match(fake, capsys):
    oeis(np.array([1, 3, 6, 10, 15]))
    assert capsys.readouterr().out == (
        "OEIS Search Results\n===================\n"
        "https://oeis.org/A000217 Triangular numbers: a(n) = binomial(n+1,2).\n")


def test_1d_no_match(fake, capsys):
    oeis(np.array([4, 8, 15, 16, 23]))
    assert capsys.readouterr().out.splitlines()[-1] == "no match"


def test_rows_of_2d_array(fake, capsys):
    assert oeis(ndplex(5)[:3]) is None
    lines = capsys.readouterr().out.splitlines()
    assert lines[:2] == ["OEIS Search Results", "==================="]
    assert lines[2:] == [
        "row 0: https://oeis.org/" + NAMES["1,1,1,1,1"],
        "row 1: https://oeis.org/" + NAMES["1,2,3,4,5"],
        "row 2: https://oeis.org/" + NAMES["1,3,6,10,15"],
    ]
    assert [c[1]["q"] for c in fake.calls] == ["1,1,1,1,1", "1,2,3,4,5",
                                               "1,3,6,10,15"]


def test_size_limits_rows(fake, capsys):
    oeis(ndplex(5), size=2)
    assert len(fake.calls) == 2
    assert capsys.readouterr().out.splitlines()[-1].startswith("row 1: ")


def test_unmatched_row(fake, capsys):
    oeis(ndplex(5)[3:4])
    assert capsys.readouterr().out.splitlines()[-1] == "row 0: no match"


def test_trim_removes_leading_and_trailing_zeros(fake):
    oeis(np.array([[0, 1, 3, 6, 10, 15, 0, 0]]), trim=True)
    oeis(np.array([0, 0, 1, 2, 3, 4, 5, 0]), trim=True)
    assert [c[1]["q"] for c in fake.calls] == ["1,3,6,10,15", "1,2,3,4,5"]


def test_untrimmed_sends_zeros(fake):
    oeis(np.array([0, 1, 2, 3, 4, 5]))
    assert fake.calls[0][1]["q"] == "0,1,2,3,4,5"


def test_triangle_rows_with_trim(fake):
    """The notebook's usage: oeis(p.as_tri(), trim=True) searches the
    triangle's rows without padding."""
    oeis(ndplex(6).as_tri()[1:3], trim=True)
    assert [c[1]["q"] for c in fake.calls] == ["1,1", "1,2,1"]


def test_plain_list_input(fake, capsys):
    oeis([1, 2, 3, 4, 5])
    assert capsys.readouterr().out.splitlines()[-1].startswith(
        "https://oeis.org/A000027")


# --- quiet=True returns instead of printing ------------------------------------

def test_quiet_returns_results(fake, capsys):
    got = oeis(ndplex(5), quiet=True)
    assert capsys.readouterr().out == ""
    assert got == [
        ("A000012", "The simplest sequence of positive numbers: the all 1's sequence."),
        ("A000027", "The positive integers."),
        ("A000217", "Triangular numbers: a(n) = binomial(n+1,2)."),
        None, None]


def test_quiet_1d_returns_one_entry(fake):
    assert oeis(np.array([1, 2, 3, 4, 5]), quiet=True) == [
        ("A000027", "The positive integers.")]
    assert oeis(np.array([4, 8, 15, 16, 23]), quiet=True) == [None]


# --- failures are reported, not hidden (N3) -------------------------------------

def test_network_error_is_reported(monkeypatch, capsys):
    monkeypatch.setattr(oeis_module, "urlopen",
                        FakeOEIS(error=TimeoutError("timed out")))
    oeis(ndplex(4)[:2])
    assert capsys.readouterr().out.splitlines()[2:] == [
        "row 0: lookup failed (timed out)", "row 1: lookup failed (timed out)"]


def test_unrecognized_response_is_reported(monkeypatch, capsys):
    monkeypatch.setattr(oeis_module, "urlopen",
                        FakeOEIS(body="<html>Service unavailable</html>"))
    oeis(np.array([1, 2, 3]))
    assert capsys.readouterr().out.splitlines()[-1] == (
        "lookup failed (unrecognized response from oeis.org)")


def test_quiet_raises(monkeypatch):
    monkeypatch.setattr(oeis_module, "urlopen",
                        FakeOEIS(body="<html>Service unavailable</html>"))
    with pytest.raises(ValueError, match="unrecognized"):
        oeis(np.array([1, 2, 3]), quiet=True)
    monkeypatch.setattr(oeis_module, "urlopen",
                        FakeOEIS(error=OSError("no route")))
    with pytest.raises(OSError, match="no route"):
        oeis(np.array([1, 2, 3]), quiet=True)


def test_rejects_3d_input(fake):
    with pytest.raises(ValueError, match="1-D or 2-D array, not 3-D$"):
        oeis(ndplex(3, edges=3))


def test_network_call_decodes_utf8(monkeypatch):
    """The one function that touches the network, with urllib's urlopen
    replaced: it passes the URL and timeout on, names ndplex and its version
    in the User-Agent header (Phase 4, C14: oeis.org refuses Python's
    default one), and decodes the answer as UTF-8, replacing undecodable
    bytes instead of failing."""
    seen = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return "café ".encode("utf-8") + b"\xff"

    def fake_urlopen(request, timeout):
        seen.update(url=request.full_url, timeout=timeout,
                    headers=dict(request.header_items()))
        return Response()

    monkeypatch.setattr(oeis_module.urllib.request, "urlopen", fake_urlopen)
    assert oeis_module.urlopen("https://oeis.org/x", 3) == "café \ufffd"
    assert seen == {
        "url": "https://oeis.org/x", "timeout": 3,
        "headers": {"User-agent": f"ndplex/{impl.__version__} "
                                  "(+https://github.com/tedteske/ndplex)"}}
