"""Shared fixtures for all skellylogs tests."""

import logging
import os
import tempfile

import pytest

import skellylogs.handlers.websocket_log_queue_handler as ws_mod


@pytest.fixture(autouse=True)
def _reset_logging_state() -> None:
    """Reset the root logger and websocket queue before each test.

    This prevents state leakage between tests — configure_logging
    modifies global state (root logger handlers/filters, the module-level
    WEBSOCKET_LOG_QUEUE singleton) that must be cleaned up.
    """
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    for f in root.filters[:]:
        root.removeFilter(f)
    root.setLevel(logging.WARNING)

    ws_mod.WEBSOCKET_LOG_QUEUE = None


@pytest.fixture()
def log_file_path() -> str:
    """Provide a temporary log file path for tests that need one."""
    return os.path.join(tempfile.mkdtemp(), "test.log")
