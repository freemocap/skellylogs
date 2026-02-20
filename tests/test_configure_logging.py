"""Tests for configure_logging and the full handler pipeline."""

import logging
import os
import tempfile
import queue as queue_module

import pytest

from skellylogs import configure_logging, LogLevels
from skellylogs.handlers.websocket_log_queue_handler import (
    get_websocket_log_queue,
    WebSocketQueueHandler,
)
from skellylogs.handlers.colored_console import ColoredConsoleHandler


def test_configure_logging_creates_handlers(log_file_path: str) -> None:
    configure_logging(level=LogLevels.DEBUG, log_file_path=log_file_path)
    root = logging.getLogger()

    handler_types = {type(h) for h in root.handlers}
    assert ColoredConsoleHandler in handler_types
    assert logging.FileHandler in handler_types
    assert WebSocketQueueHandler in handler_types


def test_configure_logging_sets_root_level(log_file_path: str) -> None:
    configure_logging(level=LogLevels.TRACE, log_file_path=log_file_path)
    root = logging.getLogger()
    assert root.level == LogLevels.TRACE.value


def test_configure_logging_writes_to_file(log_file_path: str) -> None:
    configure_logging(level=LogLevels.DEBUG, log_file_path=log_file_path)
    logger = logging.getLogger("test_file_write")
    logger.info("hello file")

    assert os.path.exists(log_file_path)
    with open(log_file_path) as f:
        content = f.read()
    assert "hello file" in content
    assert "INFO" in content


def test_configure_logging_writes_all_custom_levels_to_file(log_file_path: str) -> None:
    configure_logging(level=LogLevels.ALL, log_file_path=log_file_path)
    logger = logging.getLogger("test_custom_levels")

    logger.trace("trace msg")
    logger.success("success msg")
    logger.api("api msg")

    with open(log_file_path) as f:
        content = f.read()

    # File handler level is TRACE (5), so TRACE and above should appear
    assert "TRACE" in content
    assert "SUCCESS" in content
    assert "API" in content


def test_custom_log_methods_registered_on_logger(log_file_path: str) -> None:
    configure_logging(level=LogLevels.DEBUG, log_file_path=log_file_path)
    logger = logging.getLogger("test_methods")

    assert hasattr(logger, "loop")
    assert hasattr(logger, "trace")
    assert hasattr(logger, "success")
    assert hasattr(logger, "api")
    assert callable(logger.loop)
    assert callable(logger.trace)
    assert callable(logger.success)
    assert callable(logger.api)


def test_custom_level_names_registered() -> None:
    configure_logging(level=LogLevels.DEBUG, log_file_path=os.path.join(tempfile.mkdtemp(), "t.log"))

    assert logging.getLevelName(LogLevels.LOOP.value) == "LOOP"
    assert logging.getLevelName(LogLevels.TRACE.value) == "TRACE"
    assert logging.getLevelName(LogLevels.SUCCESS.value) == "SUCCESS"
    assert logging.getLevelName(LogLevels.API.value) == "API"


def test_websocket_queue_receives_log_records(log_file_path: str) -> None:
    configure_logging(level=LogLevels.DEBUG, log_file_path=log_file_path)
    queue = get_websocket_log_queue()

    logger = logging.getLogger("test_ws_queue")
    logger.info("ws test message")

    record = queue.get_nowait()
    assert isinstance(record, dict)
    assert record["levelname"] == "INFO"
    assert record["message"] == "ws test message"
    assert "formatted_message" in record
    assert "delta_t" in record


def test_websocket_queue_skips_low_level_records(log_file_path: str) -> None:
    configure_logging(level=LogLevels.ALL, log_file_path=log_file_path)
    queue = get_websocket_log_queue()

    logger = logging.getLogger("test_ws_level")
    logger.loop("should not appear in queue")

    with pytest.raises(queue_module.Empty):
        queue.get_nowait()


def test_get_websocket_log_queue_raises_before_configure() -> None:
    with pytest.raises(ValueError, match="not created yet"):
        get_websocket_log_queue()


def test_configure_logging_replaces_existing_handlers(log_file_path: str) -> None:
    """Calling configure_logging twice replaces handlers instead of duplicating."""
    configure_logging(level=LogLevels.DEBUG, log_file_path=log_file_path)
    first_count = len(logging.getLogger().handlers)

    log_file_path_2 = os.path.join(tempfile.mkdtemp(), "test2.log")
    configure_logging(level=LogLevels.INFO, log_file_path=log_file_path_2)
    second_count = len(logging.getLogger().handlers)

    assert second_count == first_count


def test_configure_logging_with_explicit_queue(log_file_path: str) -> None:
    """Passing an explicit ws_queue skips auto-creation."""
    import multiprocessing
    q = multiprocessing.Queue(maxsize=10)

    configure_logging(level=LogLevels.DEBUG, ws_queue=q, log_file_path=log_file_path)
    logger = logging.getLogger("test_explicit_queue")
    logger.info("explicit queue msg")

    record = q.get_nowait()
    assert record["message"] == "explicit queue msg"


def test_file_handler_level_is_trace(log_file_path: str) -> None:
    configure_logging(level=LogLevels.INFO, log_file_path=log_file_path)
    root = logging.getLogger()

    file_handlers = [h for h in root.handlers if isinstance(h, logging.FileHandler)]
    assert len(file_handlers) == 1
    assert file_handlers[0].level == LogLevels.TRACE.value
