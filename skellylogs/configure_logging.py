from __future__ import annotations
import logging
import multiprocessing

from skellylogs.default_paths import get_log_file_path
from skellylogs.handlers.websocket_log_queue_handler import create_websocket_log_queue
from skellylogs.log_levels import LogLevels
from skellylogs.logger_builder import LoggerBuilder
from skellylogs.package_log_quieters import DEFAULT_NOISY_PACKAGES, suppress_noisy_package_logs


def _add_log_method(level: LogLevels, name: str) -> None:
    def log_method(self: logging.Logger, message: str, *args: object, **kws: object) -> None:
        if self.isEnabledFor(level.value):
            self._log(level.value, message, args, **kws, stacklevel=2)

    setattr(logging.Logger, name, log_method)


def _register_custom_levels() -> None:
    """Register custom log level names and methods on logging.Logger."""
    logging.addLevelName(LogLevels.LOOP.value, "LOOP")
    logging.addLevelName(LogLevels.TRACE.value, "TRACE")
    logging.addLevelName(LogLevels.SUCCESS.value, "SUCCESS")
    logging.addLevelName(LogLevels.API.value, "API")

    _add_log_method(LogLevels.LOOP, "loop")
    _add_log_method(LogLevels.TRACE, "trace")
    _add_log_method(LogLevels.API, "api")
    _add_log_method(LogLevels.SUCCESS, "success")


def configure_logging(
    level: LogLevels,
    ws_queue: multiprocessing.Queue | None = None,
    log_file_path: str | None = None,
    suppress_packages: dict[str, int] | None = None,
) -> None:
    """Configure the root logger with colored console, file, and websocket handlers.

    Args:
        level: Minimum log level for console and websocket handlers.
        ws_queue: Multiprocessing queue for websocket log distribution.
            If None and running in the main process, a new queue is created.
            If None and running in a child process, logging setup is skipped
            (the child should receive the queue from the parent).
        log_file_path: Path for the log file. If None, defaults to
            ~/skellylogs_data/logs/<iso8601_timestamp>.log.
        suppress_packages: Map of {logger_name: level} for noisy third-party
            loggers. Defaults to DEFAULT_NOISY_PACKAGES. Pass an empty dict
            to suppress nothing.
    """
    if suppress_packages is None:
        suppress_packages = DEFAULT_NOISY_PACKAGES
    suppress_noisy_package_logs(packages=suppress_packages)

    _register_custom_levels()

    if ws_queue is None:
        # Do not create a new queue if not in the main process
        if not multiprocessing.current_process().name.lower() == "mainprocess":
            return
        ws_queue = create_websocket_log_queue()

    if log_file_path is None:
        log_file_path = get_log_file_path()

    builder = LoggerBuilder(level=level, queue=ws_queue, log_file_path=log_file_path)
    builder.configure()
