"""
Suite E -- oeis(), with the network stubbed out.

The real OEIS is never contacted. A fake `requests.get` records what was
asked and answers in OEIS's text format (lines tagged %I, %S, %N, ...;
see https://oeis.org/eishelp1.html). What is pinned is the request oeis()
builds, how it parses the answer, and what it prints.
"""
import numpy as np
import pytest

from _impl import impl, ndplex, oeis

NAMES = {
    "1,1,1,1,1": "A000012 The simplest sequence of positive numbers: the all 1's sequence.",
    "1,2,3,4,5": "A000027 The positive integers.",
    "1,3,6,10,15": "A000217 Triangular numbers: a(n) = binomial(n+1,2).",
}


class FakeResponse:
    def __init__(self, content):
        self.content = content


class FakeOEIS:
    def __init__(self):
        self.calls = []

    def __call__(self, url, params=None, **kwargs):
        self.calls.append((url, dict(params or {})))
        name = NAMES.get(params["q"])
        if name is None:  # OEIS's "no results" page has no %N line
            body = "# Greetings from The On-Line Encyclopedia\n\nNo results.\n"
        else:
            anum = name.split()[0]
            body = ("# Greetings from The On-Line Encyclopedia\n\n"
                    f"%I {anum}\n%S {anum} {params['q']}\n%N {name}\n"
                    f"%C {anum} A comment line.\n")
        return FakeResponse(body.encode("utf-8"))


@pytest.fixture
def fake(monkeypatch):
    f = FakeOEIS()
    monkeypatch.setattr(impl.requests, "get", f)
    return f


def test_request_format(fake):
    oeis(np.array([1, 2, 3, 4, 5]))
    assert fake.calls == [("http://oeis.org/search",
                           {"q": "1,2,3,4,5", "n": "1", "fmt": "text"})]


def test_1d_match(fake, capsys):
    oeis(np.array([1, 3, 6, 10, 15]))
    assert capsys.readouterr().out == (
        "OEIS Search Results\n===================\n"
        "http://oeis.org/A000217 Triangular numbers: a(n) = binomial(n+1,2).\n")


def test_1d_no_match(fake, capsys):
    oeis(np.array([4, 8, 15, 16, 23]))
    assert capsys.readouterr().out.splitlines()[-1] == "no match"


def test_rows_of_2d_array(fake, capsys):
    oeis(ndplex(5)[:3])
    lines = capsys.readouterr().out.splitlines()
    assert lines[2:] == [
        "row 0: http://oeis.org/" + NAMES["1,1,1,1,1"],
        "row 1: http://oeis.org/" + NAMES["1,2,3,4,5"],
        "row 2: http://oeis.org/" + NAMES["1,3,6,10,15"],
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
