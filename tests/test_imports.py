"""Tests that all public import paths work.

Covers the top-level API and every deep import path used by
freemocap and skellycam, so we know skellylogs is a drop-in replacement.
"""

import logging

from skellylogs import configure_logging, LogLevels, LogRecordModel
from skellylogs.configure_logging import configure_logging as configure_logging_direct
from skellylogs.log_levels import LogLevels as LogLevels_direct
from skellylogs.package_log_quieters import DEFAULT_NOISY_PACKAGES, suppress_noisy_package_logs
from skellylogs.handlers.websocket_log_queue_handler import (
    LogRecordModel as LogRecordModel_handler,
    WebSocketQueueHandler,
    get_websocket_log_queue,
    create_websocket_log_queue,
    MIN_LOG_LEVEL_FOR_WEBSOCKET,
    MAX_WEBSOCKET_LOG_QUEUE_SIZE,
)
from skellylogs.handlers.colored_console import ColoredConsoleHandler
from skellylogs.filters.delta_time import DeltaTimeFilter
from skellylogs.filters.stringify_traceback import StringifyTracebackFilter
from skellylogs.formatters.color_formatter import ColorFormatter, LOG_COLOR_CODES
from skellylogs.formatters.custom_formatter import CustomFormatter
from skellylogs.log_format_string import (
    LOG_FORMAT_STRING,
    COLOR_LOG_FORMAT_STRING,
    LOG_FORMAT_STRING_WO_PID_TID,
    LOG_POINTER_STRING,
)
from skellylogs.logger_builder import LoggerBuilder
from skellylogs.default_paths import get_log_file_path
from skellylogs.logging_color_helpers import (
    get_hashed_color,
    ensure_min_brightness,
    ensure_not_grey,
    ensure_not_red,
)


def test_top_level_reexports_are_same_objects() -> None:
    assert configure_logging is configure_logging_direct
    assert LogLevels is LogLevels_direct
    assert LogRecordModel is LogRecordModel_handler


def test_log_levels_have_expected_values() -> None:
    assert LogLevels.LOOP.value == 3
    assert LogLevels.TRACE.value == 5
    assert LogLevels.DEBUG.value == 10
    assert LogLevels.INFO.value == 20
    assert LogLevels.SUCCESS.value == 22
    assert LogLevels.API.value == 25
    assert LogLevels.WARNING.value == 30
    assert LogLevels.ERROR.value == 40
    assert LogLevels.ALL.value == 0


def test_min_log_level_for_websocket_is_trace() -> None:
    assert MIN_LOG_LEVEL_FOR_WEBSOCKET == LogLevels.TRACE.value


def test_default_noisy_packages_is_dict() -> None:
    assert isinstance(DEFAULT_NOISY_PACKAGES, dict)
    assert len(DEFAULT_NOISY_PACKAGES) > 0
    for name, level in DEFAULT_NOISY_PACKAGES.items():
        assert isinstance(name, str)
        assert isinstance(level, int)


def test_log_format_strings_contain_expected_fields() -> None:
    assert "%(message)s" in LOG_FORMAT_STRING
    assert "%(levelname)s" in LOG_FORMAT_STRING
    assert "%(delta_t)s" in LOG_FORMAT_STRING
    assert "%(process)d" in LOG_FORMAT_STRING
    assert "%(thread)d" in LOG_FORMAT_STRING
    assert LOG_POINTER_STRING in LOG_FORMAT_STRING


def test_color_log_format_has_pid_color() -> None:
    assert "%(pid_color)s" in COLOR_LOG_FORMAT_STRING
    assert "%(tid_color)s" in COLOR_LOG_FORMAT_STRING


def test_log_color_codes_cover_all_custom_levels() -> None:
    for level_name in ("LOOP", "TRACE", "DEBUG", "INFO", "SUCCESS", "API", "WARNING", "ERROR"):
        assert level_name in LOG_COLOR_CODES
