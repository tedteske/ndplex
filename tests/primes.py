"""
Offline replacement for the notebook's primes download.

The notebook's "Searching for Patterns among the Primes" section downloads
the first 1000 primes from a GitHub gist. Tests must not use the network,
so they use this sieve instead. The two agree on the values the tests use
(checked against the notebook's saved outputs, which the tests pin).
"""
import numpy as np


def first_primes(k):
    """The first k primes as a list of Python ints (k <= 1000)."""
    if not 0 <= k <= 1000:
        raise ValueError("k must be in 0..1000")
    n = 7920  # the 1000th prime is 7919
    sieve = np.ones(n, dtype=bool)
    sieve[:2] = False
    for i in range(2, int(n ** 0.5) + 1):
        if sieve[i]:
            sieve[i * i::i] = False
    return [int(x) for x in np.nonzero(sieve)[0][:k]]
