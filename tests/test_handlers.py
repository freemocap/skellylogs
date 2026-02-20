"""Tests for logging handlers."""

from __future__ import annotations

import io
import json
import logging
import multiprocessing
import queue as queue_module

import pytest

from skellylogs.handlers.websocket_log_queue_handler import (
    WebSocketQueueHandler,
    LogRecordModel,
    MAX_WEBSOCKET_LOG_QUEUE_SIZE,
    MIN_LOG_LEVEL_FOR_WEBSOCKET,
)
from skellylogs.handlers.colored_console import ColoredConsoleHandler
from skellylogs.log_levels import LogLevels

# multiprocessing.Queue on Windows uses pipes that may not flush instantly,
# so get_nowait() can raise Empty even though the item was successfully put.
# Use get(timeout=2) for all assertions that expect data.
QUEUE_TIMEOUT = 2


def _make_record(
    msg: str = "test",
    level: int = logging.INFO,
    exc_info: tuple | None = None,
) -> logging.LogRecord:
    record = logging.LogRecord(
        name="test_handler", level=level, pathname="test.py", lineno=1,
        msg=msg, args=(), exc_info=exc_info,
    )
    return record


class TestWebSocketQueueHandler:
    @pytest.fixture()
    def queue(self) -> multiprocessing.Queue:
        return multiprocessing.Queue(maxsize=100)

    @pytest.fixture()
    def handler(self, queue: multiprocessing.Queue) -> WebSocketQueueHandler:
        return WebSocketQueueHandler(queue=queue)

    def test_emits_record_as_dict(self, handler: WebSocketQueueHandler, queue: multiprocessing.Queue) -> None:
        record = _make_record("hello")
        handler.handle(record)

        payload = queue.get(timeout=QUEUE_TIMEOUT)
        assert isinstance(payload, dict)
        assert payload["message"] == "hello"
        assert payload["levelname"] == "INFO"
        assert payload["type"] == "LogRecord"
        assert payload["message_type"] == "log_record"

    def test_skips_records_below_min_level(self, handler: WebSocketQueueHandler, queue: multiprocessing.Queue) -> None:
        record = _make_record(level=LogLevels.LOOP.value)
        handler.handle(record)

        with pytest.raises(queue_module.Empty):
            queue.get_nowait()

    def test_passes_records_at_trace_level(self, handler: WebSocketQueueHandler, queue: multiprocessing.Queue) -> None:
        record = _make_record(level=LogLevels.TRACE.value)
        handler.handle(record)

        payload = queue.get(timeout=QUEUE_TIMEOUT)
        assert payload["levelno"] == LogLevels.TRACE.value

    def test_handles_full_queue_without_raising(self) -> None:
        q = multiprocessing.Queue(maxsize=1)
        handler = WebSocketQueueHandler(queue=q)

        handler.handle(_make_record("first"))
        # This should not raise even though the queue is full
        handler.handle(_make_record("second"))

        payload = q.get(timeout=QUEUE_TIMEOUT)
        assert payload["message"] == "first"

    def test_payload_contains_formatted_message(self, handler: WebSocketQueueHandler, queue: multiprocessing.Queue) -> None:
        record = _make_record("formatted test")
        handler.handle(record)

        payload = queue.get(timeout=QUEUE_TIMEOUT)
        assert "formatted_message" in payload
        assert len(payload["formatted_message"]) > 0
        assert "formatted test" in payload["formatted_message"]

    def test_payload_contains_delta_t(self, handler: WebSocketQueueHandler, queue: multiprocessing.Queue) -> None:
        record = _make_record()
        handler.handle(record)

        payload = queue.get(timeout=QUEUE_TIMEOUT)
        assert "delta_t" in payload
        assert payload["delta_t"].endswith("ms")

    def test_exception_info_serialized_as_string(self, handler: WebSocketQueueHandler, queue: multiprocessing.Queue) -> None:
        try:
            raise RuntimeError("boom")
        except RuntimeError:
            import sys
            exc_info = sys.exc_info()

        record = _make_record("error", level=logging.ERROR, exc_info=exc_info)
        handler.handle(record)

        payload = queue.get(timeout=QUEUE_TIMEOUT)
        assert payload["exc_info"] is not None
        assert "RuntimeError" in payload["exc_info"]
        assert "boom" in payload["exc_info"]

    def test_args_are_empty_list(self, handler: WebSocketQueueHandler, queue: multiprocessing.Queue) -> None:
        """Args should always be [] to avoid pickling unpicklable objects."""
        record = _make_record()
        handler.handle(record)

        payload = queue.get(timeout=QUEUE_TIMEOUT)
        assert payload["args"] == []


class TestLogRecordModel:
    @pytest.fixture()
    def sample_model(self) -> LogRecordModel:
        return LogRecordModel(
            name="test", msg="hello", args=[], levelname="INFO", levelno=20,
            pathname="test.py", filename="test.py", module="test", lineno=1,
            funcName="test_func", created=1000.0, msecs=0.0,
            relativeCreated=100.0, thread=1, threadName="MainThread",
            processName="MainProcess", process=1, delta_t="1.000ms",
            message="hello", asctime="2025-01-01T00:00:00.000",
            formatted_message="└>> hello | INFO", type="LogRecord",
        )

    def test_model_dump_returns_dict(self, sample_model: LogRecordModel) -> None:
        dumped = sample_model.model_dump()
        assert isinstance(dumped, dict)
        assert dumped["name"] == "test"
        assert dumped["msg"] == "hello"
        assert dumped["message_type"] == "log_record"

    def test_model_dump_json_returns_valid_json(self, sample_model: LogRecordModel) -> None:
        json_str = sample_model.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["name"] == "test"

    def test_round_trip_dict(self, sample_model: LogRecordModel) -> None:
        """Matches skellycam pattern: LogRecordModel(**queue.get_nowait())"""
        dumped = sample_model.model_dump()
        reconstructed = LogRecordModel(**dumped)
        assert reconstructed.name == sample_model.name
        assert reconstructed.msg == sample_model.msg
        assert reconstructed.message_type == sample_model.message_type

    def test_optional_fields_default_to_none(self) -> None:
        model = LogRecordModel(
            name="t", msg="m", args=[], levelname="INFO", levelno=20,
            pathname="", filename="", module="", lineno=0, funcName="",
            created=0.0, msecs=0.0, relativeCreated=0.0, thread=0,
            threadName="", processName="", process=0, delta_t="0ms",
            message="m", asctime="", formatted_message="", type="LogRecord",
        )
        assert model.exc_info is None
        assert model.exc_text is None
        assert model.stack_info is None


class TestColoredConsoleHandler:
    def test_writes_to_stream(self) -> None:
        stream = io.StringIO()
        handler = ColoredConsoleHandler(stream=stream)

        record = _make_record("console test")
        record.delta_t = "0.100ms"
        handler.emit(record)

        output = stream.getvalue()
        assert "console test" in output
        assert "\033[" in output  # ANSI codes present
