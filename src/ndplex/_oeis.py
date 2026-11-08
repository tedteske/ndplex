"""
oeis(): look up each row of an array in the On-Line Encyclopedia of Integer
Sequences (https://oeis.org).

Original function: Ted Teske, 2019-2024 (the notebook ndplex_array.ipynb).
Package version (https, a timeout, standard library only, failures reported
as failures, a User-Agent naming ndplex): Ted Teske with Claude (Anthropic),
2026.
"""
import urllib.parse
import urllib.request

import numpy as np

__all__ = ["oeis"]

SEARCH_URL = "https://oeis.org/search"
USER_AGENT = "ndplex/{version} (+https://github.com/tedteske/ndplex)"
_GREETING = "# Greetings from The On-Line Encyclopedia"


def urlopen(url, timeout):
    """The network call, kept separate so tests can replace it.

    The request names ndplex in its User-Agent header. oeis.org refuses
    Python's default one ("Python-urllib/3.x") with HTTP 403 (Cloudflare
    error 1010), checked from Google Colab on 7 Nov 2026.
    """
    from . import __version__  # here, not at the top: ndplex imports this module
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT.format(version=__version__)})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def _lookup(sequence, timeout):
    """Best OEIS match for `sequence` as (A-number, name), or None.

    Raises OSError if OEIS cannot be reached and ValueError if the answer
    is not in OEIS's text format.
    """
    query = urllib.parse.urlencode(
        {"q": ",".join(str(s) for s in sequence), "n": "1", "fmt": "text"})
    text = urlopen(f"{SEARCH_URL}?{query}", timeout)
    for line in text.splitlines():
        if line.startswith("%N "):
            anum, _, name = line[3:].partition(" ")
            return anum, name
    if text.lstrip().startswith(_GREETING):
        return None  # a well-formed answer with no sequence in it
    raise ValueError("unrecognized response from oeis.org")


def oeis(array, size=None, trim=False, quiet=False, timeout=10):
    """
    Search OEIS for the sequence in each row of an array.

    Parameters
    ----------
    array : array_like, 1-D or 2-D
        A 1-D array is searched as one sequence; a 2-D array row by row.
    size : int
        Number of rows to search (2-D only). Default: all rows.
    trim : bool
        If True, trim zeros from the start and end of each row first (useful
        for the rows of `as_tri`).
    quiet : bool
        If False (the default), print one line per row and return None, as
        the notebook did. If True, print nothing and return the results.
    timeout : float
        Seconds to wait for each answer from oeis.org.

    Returns
    -------
    None, or (with quiet=True) a list with one entry per row searched (one
    entry for 1-D input): (A-number, name) for the best match, or None if
    OEIS has no match.

    Raises
    ------
    With quiet=True only: OSError (including urllib.error.URLError and
    TimeoutError) if oeis.org cannot be reached, ValueError if its answer is
    not in the expected format. When printing, these are reported on the
    row's line as "lookup failed (...)" instead.

    Notes
    -----
    Each row is a separate request to oeis.org, which needs a network
    connection. Please search a few rows at a time.
    """
    array = np.asarray(array)
    if array.ndim == 1:
        rows, labels = [array], [None]
    elif array.ndim == 2:
        n = len(array) if size is None else size
        rows, labels = list(array[:n]), list(range(n))
    else:
        raise ValueError(f"oeis takes a 1-D or 2-D array, not {array.ndim}-D")

    if not quiet:
        print("OEIS Search Results")
        print("===================")

    results = []
    for row, label in zip(rows, labels):
        sequence = np.trim_zeros(row) if trim else row
        if quiet:
            results.append(_lookup(sequence, timeout))
            continue
        prefix = "" if label is None else f"row {label}: "
        try:
            match = _lookup(sequence, timeout)
        except (OSError, ValueError) as err:
            print(f"{prefix}lookup failed ({err})")
            continue
        if match is None:
            print(f"{prefix}no match")
        else:
            print(f"{prefix}https://oeis.org/{match[0]} {match[1]}")
    return results if quiet else None
