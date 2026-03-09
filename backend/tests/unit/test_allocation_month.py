"""Tests for the calculate_allocation_month utility function."""

from datetime import date

import pytest

from app.modules.income.models import calculate_allocation_month


class TestCalculateAllocationMonth:
    """Suite for calculate_allocation_month(date_received, allocation_type)."""

    # ── same_month ──────────────────────────────────────────────────

    def test_same_month_mid_month(self) -> None:
        result = calculate_allocation_month(date(2026, 3, 15), "same_month")
        assert result == date(2026, 3, 1)

    def test_same_month_first_day(self) -> None:
        result = calculate_allocation_month(date(2026, 3, 1), "same_month")
        assert result == date(2026, 3, 1)

    def test_same_month_last_day(self) -> None:
        result = calculate_allocation_month(date(2026, 3, 31), "same_month")
        assert result == date(2026, 3, 1)

    def test_same_month_january(self) -> None:
        result = calculate_allocation_month(date(2026, 1, 20), "same_month")
        assert result == date(2026, 1, 1)

    def test_same_month_december(self) -> None:
        result = calculate_allocation_month(date(2026, 12, 25), "same_month")
        assert result == date(2026, 12, 1)

    # ── next_month ──────────────────────────────────────────────────

    def test_next_month_mid_month(self) -> None:
        result = calculate_allocation_month(date(2026, 3, 15), "next_month")
        assert result == date(2026, 4, 1)

    def test_next_month_last_day_of_month(self) -> None:
        result = calculate_allocation_month(date(2026, 3, 31), "next_month")
        assert result == date(2026, 4, 1)

    def test_next_month_first_day(self) -> None:
        result = calculate_allocation_month(date(2026, 3, 1), "next_month")
        assert result == date(2026, 4, 1)

    def test_next_month_december_rolls_to_january(self) -> None:
        result = calculate_allocation_month(date(2026, 12, 25), "next_month")
        assert result == date(2027, 1, 1)

    def test_next_month_january(self) -> None:
        result = calculate_allocation_month(date(2026, 1, 31), "next_month")
        assert result == date(2026, 2, 1)

    # ── leap year ───────────────────────────────────────────────────

    def test_leap_year_february_same_month(self) -> None:
        result = calculate_allocation_month(date(2028, 2, 29), "same_month")
        assert result == date(2028, 2, 1)

    def test_leap_year_february_next_month(self) -> None:
        result = calculate_allocation_month(date(2028, 2, 29), "next_month")
        assert result == date(2028, 3, 1)

    # ── invariant: result is always 1st of month ────────────────────

    @pytest.mark.parametrize("day", range(1, 29))
    @pytest.mark.parametrize("allocation_type", ["same_month", "next_month"])
    def test_result_always_first_of_month(self, day: int, allocation_type: str) -> None:
        result = calculate_allocation_month(date(2026, 6, day), allocation_type)
        assert result.day == 1, f"Expected day=1, got day={result.day}"

    # ── real-world scenario from requirements ───────────────────────

    def test_salary_march_31_allocated_to_april(self) -> None:
        """Salary received March 31 → allocated to April."""
        result = calculate_allocation_month(date(2026, 3, 31), "next_month")
        assert result == date(2026, 4, 1)

    def test_salary_march_15_same_month(self) -> None:
        """Mid-month income stays in the same month."""
        result = calculate_allocation_month(date(2026, 3, 15), "same_month")
        assert result == date(2026, 3, 1)
