"""Tests for package_log_quieters."""

import logging
import os
import tempfile

from skellylogs import configure_logging, LogLevels
from skellylogs.package_log_quieters import DEFAULT_NOISY_PACKAGES, suppress_noisy_package_logs


def test_suppress_noisy_package_logs_sets_levels() -> None:
    packages = {"fake_pkg_a": logging.ERROR, "fake_pkg_b": logging.WARNING}
    suppress_noisy_package_logs(packages=packages)

    assert logging.getLogger("fake_pkg_a").level == logging.ERROR
    assert logging.getLogger("fake_pkg_b").level == logging.WARNING


def test_suppress_empty_dict_changes_nothing() -> None:
    logger = logging.getLogger("untouched_pkg")
    original_level = logger.level
    suppress_noisy_package_logs(packages={})
    assert logger.level == original_level


def test_default_noisy_packages_applied_by_default() -> None:
    log_path = os.path.join(tempfile.mkdtemp(), "test.log")
    configure_logging(level=LogLevels.DEBUG, log_file_path=log_path)

    for name, expected_level in DEFAULT_NOISY_PACKAGES.items():
        actual = logging.getLogger(name).level
        assert actual == expected_level, (
            f"Logger {name!r}: expected level {expected_level}, got {actual}"
        )


def test_custom_suppress_packages_override_defaults() -> None:
    log_path = os.path.join(tempfile.mkdtemp(), "test.log")
    custom = {"my_noisy_lib": logging.CRITICAL}
    configure_logging(level=LogLevels.DEBUG, log_file_path=log_path, suppress_packages=custom)

    assert logging.getLogger("my_noisy_lib").level == logging.CRITICAL
    # matplotlib should NOT have been suppressed since we replaced defaults entirely
    # (it would only be suppressed if it was in our custom dict)


def test_merged_suppress_packages() -> None:
    log_path = os.path.join(tempfile.mkdtemp(), "test.log")
    merged = DEFAULT_NOISY_PACKAGES | {"cv2": logging.WARNING}
    configure_logging(level=LogLevels.DEBUG, log_file_path=log_path, suppress_packages=merged)

    assert logging.getLogger("cv2").level == logging.WARNING
    assert logging.getLogger("matplotlib").level == logging.WARNING


def test_empty_suppress_packages_suppresses_nothing() -> None:
    # Reset a logger we know defaults would touch
    logging.getLogger("httpx").setLevel(logging.DEBUG)

    log_path = os.path.join(tempfile.mkdtemp(), "test.log")
    configure_logging(level=LogLevels.DEBUG, log_file_path=log_path, suppress_packages={})

    assert logging.getLogger("httpx").level == logging.DEBUG
