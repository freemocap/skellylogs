"""Tests for LoggerBuilder."""

import logging
import multiprocessing

from skellylogs.logger_builder import LoggerBuilder
from skellylogs.log_levels import LogLevels
from skellylogs.handlers.websocket_log_queue_handler import WebSocketQueueHandler
from skellylogs.handlers.colored_console import ColoredConsoleHandler
from skellylogs.filters.stringify_traceback import StringifyTracebackFilter


def test_configure_adds_three_handlers_with_queue(log_file_path: str) -> None:
    queue = multiprocessing.Queue(maxsize=10)
    builder = LoggerBuilder(level=LogLevels.DEBUG, queue=queue, log_file_path=log_file_path)
    builder.configure()

    root = logging.getLogger()
    handler_types = {type(h) for h in root.handlers}
    assert ColoredConsoleHandler in handler_types
    assert logging.FileHandler in handler_types
    assert WebSocketQueueHandler in handler_types


def test_configure_adds_two_handlers_without_queue(log_file_path: str) -> None:
    builder = LoggerBuilder(level=LogLevels.DEBUG, queue=None, log_file_path=log_file_path)
    builder.configure()

    root = logging.getLogger()
    handler_types = {type(h) for h in root.handlers}
    assert ColoredConsoleHandler in handler_types
    assert logging.FileHandler in handler_types
    assert WebSocketQueueHandler not in handler_types


def test_configure_sets_root_level(log_file_path: str) -> None:
    builder = LoggerBuilder(level=LogLevels.TRACE, queue=None, log_file_path=log_file_path)
    builder.configure()

    assert logging.getLogger().level == LogLevels.TRACE.value


def test_configure_adds_stringify_traceback_filter(log_file_path: str) -> None:
    builder = LoggerBuilder(level=LogLevels.DEBUG, queue=None, log_file_path=log_file_path)
    builder.configure()

    root = logging.getLogger()
    filter_types = {type(f) for f in root.filters}
    assert StringifyTracebackFilter in filter_types


def test_configure_clears_previous_handlers(log_file_path: str) -> None:
    root = logging.getLogger()

    # Snapshot before: pytest may have its own handlers attached
    baseline = len(root.handlers)

    # Add a dummy handler on top of whatever pytest has
    root.addHandler(logging.StreamHandler())
    assert len(root.handlers) == baseline + 1

    # configure() should clear everything and add its own set
    builder = LoggerBuilder(level=LogLevels.DEBUG, queue=None, log_file_path=log_file_path)
    builder.configure()

    # After configure, none of the old handlers should remain —
    # only our ColoredConsoleHandler and FileHandler
    handler_types = {type(h) for h in root.handlers}
    assert ColoredConsoleHandler in handler_types
    assert logging.FileHandler in handler_types


def test_file_handler_uses_provided_path(log_file_path: str) -> None:
    import os
    builder = LoggerBuilder(level=LogLevels.DEBUG, queue=None, log_file_path=log_file_path)
    builder.configure()

    logger = logging.getLogger("test_file_path")
    logger.info("path test")

    assert os.path.exists(log_file_path)
    with open(log_file_path) as f:
        assert "path test" in f.read()
