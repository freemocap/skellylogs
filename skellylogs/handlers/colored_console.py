import logging
import sys
from typing import TextIO

from tqdm import tqdm

from ..filters.delta_time import DeltaTimeFilter
from ..formatters.color_formatter import ColorFormatter
from ..log_format_string import COLOR_LOG_FORMAT_STRING


class ColoredConsoleHandler(logging.StreamHandler):
    """Colorized console output with Δt and process/thread coloring"""

    def __init__(self, stream: TextIO = sys.stdout) -> None:
        super().__init__(stream)
        self.setFormatter(ColorFormatter(COLOR_LOG_FORMAT_STRING))
        self.addFilter(DeltaTimeFilter())

    def emit(self, record: logging.LogRecord) -> None:
        """Write log messages above active terminal progress bars."""
        with tqdm.external_write_mode(file=self.stream):
            super().emit(record)
