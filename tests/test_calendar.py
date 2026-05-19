"""日历计算模块单元测试"""

import pytest
from todo_manager.engine.calendar_utils import (
    get_weekday_cn,
    get_month_grid,
    is_date_in_range,
)


class TestGetWeekdayCn:
    def test_monday(self):
        assert get_weekday_cn("2026-04-06") == "星期一"

    def test_tuesday(self):
        assert get_weekday_cn("2026-04-07") == "星期二"

    def test_wednesday(self):
        assert get_weekday_cn("2026-04-08") == "星期三"

    def test_thursday(self):
        assert get_weekday_cn("2026-04-09") == "星期四"

    def test_friday(self):
        assert get_weekday_cn("2026-04-10") == "星期五"

    def test_saturday(self):
        assert get_weekday_cn("2026-04-11") == "星期六"

    def test_sunday(self):
        assert get_weekday_cn("2026-04-12") == "星期日"

    def test_invalid_format(self):
        with pytest.raises(ValueError):
            get_weekday_cn("2026/04/06")

    def test_nonexistent_date(self):
        with pytest.raises(ValueError):
            get_weekday_cn("2026-02-30")

    def test_empty_string(self):
        with pytest.raises(ValueError):
            get_weekday_cn("")


class TestGetMonthGrid:
    def test_april_2026_structure(self):
        """2026-04: starts Wednesday, has 30 days, fits 5 weeks"""
        grid = get_month_grid(2026, 4)
        assert len(grid) == 5
        for row in grid:
            assert len(row) == 7

    def test_first_cell_is_none(self):
        """April 2026 starts on Wednesday → first three cells (Mon-Wed prior) are None"""
        grid = get_month_grid(2026, 4)
        assert grid[0][0] is None  # Monday before April
        assert grid[0][1] is None  # Tuesday before April
        assert grid[0][2] is not None  # April 1 = Wednesday

    def test_first_date_is_correct(self):
        grid = get_month_grid(2026, 4)
        first_cell = grid[0][2]
        assert first_cell is not None
        assert first_cell["date"] == "2026-04-01"

    def test_last_date_is_correct(self):
        grid = get_month_grid(2026, 4)
        # April 30 is a Thursday → should be in first row, column 6 (0-indexed)
        last_row = grid[-1]
        non_none = [c for c in last_row if c is not None]
        last_cell = non_none[-1]
        assert last_cell["date"] == "2026-04-30"

    def test_weekday_in_grid(self):
        grid = get_month_grid(2026, 4)
        cell = grid[0][2]
        assert cell is not None
        assert cell["weekday"] == "星期三"

    def test_february_leap_year(self):
        """2024-02 is a leap year with 29 days"""
        grid = get_month_grid(2024, 2)
        all_dates = []
        for row in grid:
            for cell in row:
                if cell:
                    all_dates.append(cell["date"])
        assert "2024-02-29" in all_dates

    def test_february_non_leap(self):
        """2025-02 has 28 days"""
        grid = get_month_grid(2025, 2)
        all_dates = []
        for row in grid:
            for cell in row:
                if cell:
                    all_dates.append(cell["date"])
        assert "2025-02-29" not in all_dates

    def test_31_day_month(self):
        grid = get_month_grid(2026, 1)
        all_dates = []
        for row in grid:
            for cell in row:
                if cell:
                    all_dates.append(cell["date"])
        assert len(all_dates) == 31


class TestIsDateInRange:
    def test_inside_range(self):
        assert is_date_in_range("2026-04-15", "2026-04-01", "2026-04-30")

    def test_at_start_boundary(self):
        assert is_date_in_range("2026-04-01", "2026-04-01", "2026-04-30")

    def test_at_end_boundary(self):
        assert is_date_in_range("2026-04-30", "2026-04-01", "2026-04-30")

    def test_before_start(self):
        assert not is_date_in_range("2026-03-31", "2026-04-01", "2026-04-30")

    def test_after_end(self):
        assert not is_date_in_range("2026-05-01", "2026-04-01", "2026-04-30")

    def test_single_day_range(self):
        """start == end"""
        assert is_date_in_range("2026-04-15", "2026-04-15", "2026-04-15")
        assert not is_date_in_range("2026-04-14", "2026-04-15", "2026-04-15")
