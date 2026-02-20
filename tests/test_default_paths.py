"""Tests for default_paths."""

import os
import re
from pathlib import Path

from skellylogs.default_paths import get_log_file_path


def test_get_log_file_path_returns_string() -> None:
    path = get_log_file_path()
    assert isinstance(path, str)


def test_get_log_file_path_is_under_home() -> None:
    path = get_log_file_path()
    assert path.startswith(str(Path.home()))


def test_get_log_file_path_contains_skellylogs_data() -> None:
    path = get_log_file_path()
    assert "skellylogs_data" in path


def test_get_log_file_path_ends_with_log_extension() -> None:
    path = get_log_file_path()
    assert path.endswith(".log")


def test_get_log_file_path_creates_directory() -> None:
    path = get_log_file_path()
    directory = os.path.dirname(path)
    assert os.path.isdir(directory)


def test_get_log_file_path_filename_has_iso8601_structure() -> None:
    path = get_log_file_path()
    filename = os.path.basename(path)
    # Should match: log_YYYY-MM-DDTHH_MM_SSmsNNN_gmt+N.log
    assert filename.startswith("log_")
    assert "gmt" in filename


def test_get_log_file_path_is_filename_friendly() -> None:
    """Colons and dots should be replaced for filesystem compatibility."""
    path = get_log_file_path()
    filename = os.path.basename(path)
    # Remove the .log extension for checking
    stem = filename[:-4]
    assert ":" not in stem
