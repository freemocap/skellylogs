"""Tests for logging_color_helpers."""

from skellylogs.logging_color_helpers import (
    ensure_min_brightness,
    ensure_not_grey,
    ensure_not_red,
    get_hashed_color,
)


class TestEnsureMinBrightness:
    def test_value_below_threshold_is_raised(self) -> None:
        assert ensure_min_brightness(50, threshold=100) == 100

    def test_value_above_threshold_unchanged(self) -> None:
        assert ensure_min_brightness(200, threshold=100) == 200

    def test_value_at_threshold_unchanged(self) -> None:
        assert ensure_min_brightness(100, threshold=100) == 100


class TestEnsureNotGrey:
    def test_grey_color_gets_saturated(self) -> None:
        r, g, b = ensure_not_grey(120, 120, 120, threshold_diff=100)
        assert max(r, g, b) == 255

    def test_already_saturated_unchanged(self) -> None:
        r, g, b = ensure_not_grey(255, 50, 50, threshold_diff=100)
        assert r == 255 and g == 50 and b == 50


class TestEnsureNotRed:
    def test_too_red_gets_adjusted(self) -> None:
        r, g, b = ensure_not_red(255, 50, 50, threshold_diff=100)
        assert r < 255
        assert max(g, b) == 255

    def test_balanced_color_unchanged(self) -> None:
        r, g, b = ensure_not_red(100, 150, 200, threshold_diff=100)
        assert (r, g, b) == (100, 150, 200)


class TestGetHashedColor:
    def test_returns_ansi_escape(self) -> None:
        color = get_hashed_color(12345)
        assert color.startswith("\033[38;2;")
        assert color.endswith("m")

    def test_deterministic_for_same_input(self) -> None:
        assert get_hashed_color(42) == get_hashed_color(42)

    def test_different_inputs_produce_different_colors(self) -> None:
        colors = {get_hashed_color(i) for i in range(1000)}
        assert len(colors) > 10
