"""Tests for logging filters."""

import logging
import time
import traceback

from skellylogs.filters.delta_time import DeltaTimeFilter
from skellylogs.filters.stringify_traceback import StringifyTracebackFilter


class TestDeltaTimeFilter:
    def test_adds_delta_t_attribute(self) -> None:
        filt = DeltaTimeFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="hi", args=(), exc_info=None,
        )
        result = filt.filter(record)
        assert result is True
        assert hasattr(record, "delta_t")
        assert record.delta_t.endswith("ms")

    def test_delta_t_increases_with_delay(self) -> None:
        filt = DeltaTimeFilter()

        record1 = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="first", args=(), exc_info=None,
        )
        filt.filter(record1)

        time.sleep(0.05)

        record2 = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="second", args=(), exc_info=None,
        )
        filt.filter(record2)

        delta_ms = float(record2.delta_t.replace("ms", ""))
        assert delta_ms >= 40.0, f"Expected >= 40ms, got {delta_ms}ms"

    def test_always_returns_true(self) -> None:
        filt = DeltaTimeFilter()
        for _ in range(10):
            record = logging.LogRecord(
                name="test", level=logging.INFO, pathname="", lineno=0,
                msg="msg", args=(), exc_info=None,
            )
            assert filt.filter(record) is True


class TestStringifyTracebackFilter:
    def test_converts_exc_info_to_exc_text(self) -> None:
        filt = StringifyTracebackFilter()
        try:
            raise ValueError("test error")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="", lineno=0,
            msg="error", args=(), exc_info=exc_info,
        )
        assert record.exc_info is not None
        assert record.exc_info[2] is not None

        result = filt.filter(record)
        assert result is True
        assert record.exc_info is None
        assert record.exc_text is not None
        assert "ValueError" in record.exc_text
        assert "test error" in record.exc_text

    def test_does_not_overwrite_existing_exc_text(self) -> None:
        filt = StringifyTracebackFilter()
        try:
            raise RuntimeError("boom")
        except RuntimeError:
            import sys
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="", lineno=0,
            msg="error", args=(), exc_info=exc_info,
        )
        record.exc_text = "pre-existing text"

        filt.filter(record)
        assert record.exc_text == "pre-existing text"

    def test_passes_through_records_without_exc_info(self) -> None:
        filt = StringifyTracebackFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="normal", args=(), exc_info=None,
        )
        result = filt.filter(record)
        assert result is True
        assert record.exc_text is None
