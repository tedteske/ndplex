"""Shared test setup: no network; platform details in the report header."""
import platform
import socket
import sys

import numpy as np

import pytest


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """Tests must never touch the network (oeis is stubbed where tested)."""
    def refuse(*args, **kwargs):
        raise OSError("network access is disabled in the test suite")
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)


def pytest_report_header(config):
    """What the platform-dependent tests (tests/test_platform.py) depend on."""
    from _impl import impl  # honours NDPLEX_IMPL_PATH (mutation check)
    return (f"ndplex {impl.__version__} from {impl.__file__}; "
            f"numpy {np.__version__}; default int {np.dtype(int)}; "
            f"{platform.system()} {platform.machine()}; "
            f"Python {sys.version.split()[0]}")
