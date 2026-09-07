"""Console logs and active progress share one terminal cursor."""

import io
import logging
import unittest
from unittest.mock import patch

from tqdm import tqdm

from skellylogs.handlers.colored_console import ColoredConsoleHandler


class ConsoleProgressTests(unittest.TestCase):
    def test_log_clears_and_redraws_each_active_bar(self) -> None:
        terminal = io.StringIO()
        handler = ColoredConsoleHandler(stream=terminal)
        handler.setFormatter(logging.Formatter("%(message)s"))
        record = logging.LogRecord("test", logging.INFO, __file__, 1, "pipeline message", (), None)
        with tqdm(total=3, desc="camera-one", file=terminal, disable=False) as first, \
                tqdm(total=3, desc="camera-two", file=terminal, disable=False) as second:
            with patch.object(first, "clear", wraps=first.clear) as clear_first, \
                    patch.object(second, "clear", wraps=second.clear) as clear_second, \
                    patch.object(first, "refresh", wraps=first.refresh) as redraw_first, \
                    patch.object(second, "refresh", wraps=second.refresh) as redraw_second:
                handler.handle(record)
                clear_first.assert_called_once()
                clear_second.assert_called_once()
                redraw_first.assert_called_once()
                redraw_second.assert_called_once()
            text = terminal.getvalue()
            self.assertEqual(text.count("pipeline message"), 1)
            self.assertGreater(text.rfind("camera-one"), text.index("pipeline message"))
            self.assertGreater(text.rfind("camera-two"), text.index("pipeline message"))

    def test_redirected_output_has_no_animated_progress(self) -> None:
        output = io.StringIO()
        with tqdm(total=3, file=output, disable=None) as progress:
            for _ in range(3):
                progress.update(1)
        self.assertEqual(output.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
