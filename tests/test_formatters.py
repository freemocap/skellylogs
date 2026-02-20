"""Tests for logging formatters."""

import logging

from skellylogs.formatters.custom_formatter import CustomFormatter
from skellylogs.formatters.color_formatter import ColorFormatter, LOG_COLOR_CODES
from skellylogs.log_format_string import LOG_FORMAT_STRING, COLOR_LOG_FORMAT_STRING


def _make_record(msg: str = "test message", level: int = logging.INFO) -> logging.LogRecord:
    record = logging.LogRecord(
        name="test_logger", level=level, pathname="test.py", lineno=42,
        msg=msg, args=(), exc_info=None,
    )
    record.delta_t = "1.234ms"
    return record


class TestCustomFormatter:
    def test_format_contains_message(self) -> None:
        fmt = CustomFormatter(format_string=LOG_FORMAT_STRING)
        record = _make_record("hello world")
        output = fmt.format(record)
        assert "hello world" in output

    def test_format_contains_timestamp_with_milliseconds(self) -> None:
        fmt = CustomFormatter(format_string=LOG_FORMAT_STRING)
        record = _make_record()
        output = fmt.format(record)
        # Timestamp format: 2025-02-20T14:30:01.123
        assert "T" in output
        # Should have millisecond precision (3 digits after dot)
        import re
        assert re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}", output)

    def test_format_contains_level_name(self) -> None:
        fmt = CustomFormatter(format_string=LOG_FORMAT_STRING)
        record = _make_record(level=logging.WARNING)
        output = fmt.format(record)
        assert "WARNING" in output


class TestColorFormatter:
    def test_format_contains_ansi_codes(self) -> None:
        fmt = ColorFormatter(format_string=COLOR_LOG_FORMAT_STRING)
        record = _make_record()
        # ColorFormatter needs pid_color and tid_color, which it sets itself
        output = fmt.format(record)
        assert "\033[" in output

    def test_format_contains_message(self) -> None:
        fmt = ColorFormatter(format_string=COLOR_LOG_FORMAT_STRING)
        record = _make_record("colored msg")
        output = fmt.format(record)
        assert "colored msg" in output

    def test_does_not_mutate_original_record(self) -> None:
        fmt = ColorFormatter(format_string=COLOR_LOG_FORMAT_STRING)
        record = _make_record("original")
        original_msg = record.msg
        fmt.format(record)
        assert record.msg == original_msg

    def test_formats_exception_info(self) -> None:
        fmt = ColorFormatter(format_string=COLOR_LOG_FORMAT_STRING)
        try:
            raise ValueError("test exception")
        except ValueError:
            import sys
            exc_info = sys.exc_info()

        record = _make_record("error occurred")
        record.exc_info = exc_info
        output = fmt.format(record)
        assert "ValueError" in output
        assert "test exception" in output
