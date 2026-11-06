"""Shared test setup: no network."""
import socket

import pytest


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """Tests must never touch the network (oeis is stubbed where tested)."""
    def refuse(*args, **kwargs):
        raise OSError("network access is disabled in the test suite")
    monkeypatch.setattr(socket.socket, "connect", refuse)
    monkeypatch.setattr(socket, "create_connection", refuse)
