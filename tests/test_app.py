import datetime
from unittest.mock import patch

import pytest

from pydantic import ValidationError

import wenfire.fire
from wenfire.fire import (
    InputData,
    Results,
    Summary,
    calculate_results_for_month,
    interpolate,
)


# Fixtures
@pytest.fixture
def input_data() -> InputData:
    return InputData(
        growth_rate=5.0,
        current_nw=100000.0,
        spending_per_month=3000.0,
        inflation=2.0,
        annual_salary_increase=3.0,
        income_per_month=5000.0,
        extra_income=500.0,
        date_of_birth=datetime.date(1990, 1, 1),
        safe_withdraw_rate=4.0,
    )


# Mock today's date for consistent testing
@pytest.fixture(autouse=True)
def fixed_today():
    """
    A pytest fixture that mocks datetime.date.today() to return 2024-04-01.
    """
    fixed_date = datetime.date(2024, 4, 1)
    with patch.object(wenfire.fire, "_today", return_value=fixed_date):
        yield fixed_date


# Tests for InputData
def test_input_data_age_at(input_data: InputData) -> None:
    target_date = datetime.date(2024, 4, 1)
    age = input_data.age_at(target_date)
    expected_age = 34.25  # From 1990-01-01 to 2024-04-01
    assert abs(age - expected_age) < 0.01, f"Expected age {expected_age}, got {age}"


def test_input_data_age(input_data: InputData) -> None:
    age = input_data.age
    expected_age = 34.25  # From 1990-01-01 to 2024-04-01
    assert abs(age - expected_age) < 0.01, f"Expected age {expected_age}, got {age}"


def test_input_data_saving_per_month(input_data: InputData) -> None:
    expected_saving = (
        input_data.income_per_month
        + input_data.extra_income
        - input_data.spending_per_month
    )
    assert (
        input_data.saving_per_month == expected_saving
    ), "Incorrect saving_per_month calculation"


def test_input_data_monthly_growth_rate(input_data: InputData) -> None:
    expected = (1 + input_data.growth_rate / 100) ** (1 / 12)
    assert (
        abs(input_data.monthly_growth_rate - expected) < 1e-6
    ), "Incorrect monthly_growth_rate calculation"


def test_input_data_monthly_inflation(input_data: InputData) -> None:
    expected = (1 + input_data.inflation / 100) ** (1 / 12)
    assert (
        abs(input_data.monthly_inflation - expected) < 1e-6
    ), "Incorrect monthly_inflation calculation"


def test_input_data_monthly_salary_increase_rate(input_data: InputData) -> None:
    expected = (1 + input_data.annual_salary_increase / 100) ** (1 / 12)
    assert (
        abs(input_data.monthly_salary_increase_rate - expected) < 1e-6
    ), "Incorrect monthly_salary_increase_rate calculation"


# Tests for Results
def test_results_initial(input_data: InputData) -> None:
    r = Results(
        months=0,
        nw=input_data.current_nw,
        income=input_data.income_per_month,
        extra_income=input_data.extra_income,
        spending=input_data.spending_per_month,
        delta_nw=0.0,
        total_saved=input_data.current_nw,
        input_data=input_data,
    )
    assert r.months == 0
    assert r.nw == input_data.current_nw
    assert r.income == input_data.income_per_month
    assert r.extra_income == input_data.extra_income
    assert r.spending == input_data.spending_per_month
    assert r.delta_nw == 0.0
    assert r.total_saved == input_data.current_nw


def test_results_next_month(input_data: InputData) -> None:
    r = Results(
        months=0,
        nw=input_data.current_nw,
        income=input_data.income_per_month,
        extra_income=input_data.extra_income,
        spending=input_data.spending_per_month,
        delta_nw=0.0,
        total_saved=input_data.current_nw,
        input_data=input_data,
    )
    next_r = r.next_month()
    expected_nw = r.nw + r.investment_profits + r.saving
    expected_income = r.income * input_data.monthly_salary_increase_rate
    expected_spending = r.spending * input_data.monthly_inflation
    expected_delta_nw = expected_nw - r.nw
    expected_total_saved = r.total_saved + r.saving

    assert next_r.months == 1
    assert abs(next_r.nw - expected_nw) < 1e-6, "Incorrect nw after next_month"
    assert (
        abs(next_r.income - expected_income) < 1e-6
    ), "Incorrect income after next_month"
    assert (
        abs(next_r.spending - expected_spending) < 1e-6
    ), "Incorrect spending after next_month"
    assert (
        abs(next_r.delta_nw - expected_delta_nw) < 1e-6
    ), "Incorrect delta_nw after next_month"
    assert (
        abs(next_r.total_saved - expected_total_saved) < 1e-6
    ), "Incorrect total_saved after next_month"


# Tests for utility functions


def test_interpolate() -> None:
    assert interpolate(0, 10, 0.5) == 5.0, "Interpolation failed for middle fraction"
    assert (
        interpolate(10, 20, 0.25) == 12.5
    ), "Interpolation failed for quarter fraction"
    assert interpolate(-5, 5, 0.5) == 0.0, "Interpolation failed with negative numbers"
    assert interpolate(100, 200, 0) == 100, "Interpolation failed for fraction 0"
    assert interpolate(100, 200, 1) == 200, "Interpolation failed for fraction 1"


# Tests for Summary


def test_summary_from_results_no_retirement(input_data: InputData) -> None:
    # Create a list of Results where the retirement condition is never met
    r = Results(
        months=0,
        nw=100000.0,
        income=5000.0,
        extra_income=500.0,
        spending=3000.0,
        delta_nw=0.0,
        total_saved=100000.0,
        input_data=input_data,
    )
    results = [r] + [r.next_month() for _ in range(100)]
    summary = Summary.from_results(results)
    assert (
        summary is None
    ), "Summary should be None when retirement condition is not met"


# Tests for calculate_results_for_month
def test_calculate_results_for_month_no_target(input_data: InputData) -> None:
    results = calculate_results_for_month(input_data)
    assert len(results) > 0, "Results should not be empty"
    # Check first result
    first = results[0]
    assert first.months == 0
    assert first.nw == input_data.current_nw
    assert first.income == input_data.income_per_month
    assert first.spending == input_data.spending_per_month


def test_calculate_results_for_month_with_target_int(input_data: InputData) -> None:
    target_months = 24
    results = calculate_results_for_month(input_data, target=target_months)
    assert len(results) == 25, f"Expected 25 months, got {len(results)}"


def test_calculate_results_for_month_retirement_condition(
    input_data: InputData,
) -> None:
    # Modify input_data to meet retirement condition quickly
    input_data.spending_per_month = 4000.0  # Increase spending
    input_data.extra_income = 2000.0  # Increase extra income to make saving high

    results = calculate_results_for_month(input_data)
    # Expect retirement condition met early
    assert len(results) < 100 * 12, "Retirement condition should have been met early"


# Tests for Validation
def test_input_data_validation() -> None:
    with pytest.raises(ValidationError):
        InputData(
            growth_rate="five",  # Invalid type
            current_nw=100000.0,
            spending_per_month=3000.0,
            inflation=2.0,
            annual_salary_increase=3.0,
            income_per_month=5000.0,
            extra_income=500.0,
            date_of_birth="1990-01-01",  # Invalid type, should be datetime.date
        )


# Additional edge case tests
def test_age_at_leap_year(input_data: InputData) -> None:
    birth_date = datetime.date(2000, 2, 29)
    input_data.date_of_birth = birth_date
    target_date = datetime.date(2024, 2, 28)
    age = input_data.age_at(target_date)
    expected_age = 23.99726  # Approximately, not reaching the 24th birthday
    assert abs(age - expected_age) < 0.01, f"Expected age {expected_age}, got {age}"


def test_interpolate_fraction_out_of_bounds() -> None:
    # Even though the function does not restrict fraction, test behavior
    assert (
        interpolate(0, 10, -0.5) == -5.0
    ), "Interpolation failed for negative fraction"
    assert interpolate(0, 10, 1.5) == 15.0, "Interpolation failed for fraction >1"


# Tests for post-FIRE spending feature
def test_post_fire_spending_uses_lower_target_for_fire() -> None:
    """Test that FIRE is calculated based on post_fire_spending when set."""
    # Create input where current spending is high but target spending is low
    input_data = InputData(
        growth_rate=7.0,
        current_nw=500000.0,  # $500k
        spending_per_month=5000.0,  # $5k/month current spending
        inflation=2.0,
        annual_salary_increase=3.0,
        income_per_month=8000.0,
        extra_income=0.0,
        date_of_birth=datetime.date(1990, 1, 1),
        safe_withdraw_rate=4.0,
        post_fire_spending_per_month=2000.0,  # $2k/month target (cheaper country)
    )

    results = calculate_results_for_month(input_data)
    first_result = results[0]

    # Verify post_fire_spending is set
    assert first_result.post_fire_spending == 2000.0

    # fire_spending_target should return post_fire_spending when set
    assert first_result.fire_spending_target == 2000.0

    # safe_withdraw_minus_spending should compare against target, not current
    # With $500k and 4% SWR: yearly = $20k, monthly = $1666.67
    # This is less than $2000 target, so should be negative
    expected_swr_monthly = 500000.0 * 0.04 / 12
    expected_diff = expected_swr_monthly - 2000.0
    assert abs(first_result.safe_withdraw_minus_spending - expected_diff) < 0.01


def test_post_fire_spending_none_uses_current_spending() -> None:
    """Test that without post_fire_spending, current spending is used for FIRE."""
    input_data = InputData(
        growth_rate=7.0,
        current_nw=500000.0,
        spending_per_month=3000.0,
        inflation=2.0,
        annual_salary_increase=3.0,
        income_per_month=8000.0,
        extra_income=0.0,
        date_of_birth=datetime.date(1990, 1, 1),
        safe_withdraw_rate=4.0,
        post_fire_spending_per_month=None,  # No target - use current spending
    )

    results = calculate_results_for_month(input_data)
    first_result = results[0]

    # Verify post_fire_spending is None
    assert first_result.post_fire_spending is None

    # fire_spending_target should fall back to current spending
    assert first_result.fire_spending_target == 3000.0

    # safe_withdraw_minus_spending should compare against current spending
    expected_swr_monthly = 500000.0 * 0.04 / 12
    expected_diff = expected_swr_monthly - 3000.0
    assert abs(first_result.safe_withdraw_minus_spending - expected_diff) < 0.01


def test_post_fire_spending_earlier_fire_date() -> None:
    """Test that lower post_fire_spending leads to earlier FIRE date."""
    base_input = InputData(
        growth_rate=7.0,
        current_nw=200000.0,
        spending_per_month=4000.0,
        inflation=2.0,
        annual_salary_increase=3.0,
        income_per_month=7000.0,
        extra_income=0.0,
        date_of_birth=datetime.date(1990, 1, 1),
        safe_withdraw_rate=4.0,
    )

    # Calculate with current spending as target
    results_current = calculate_results_for_month(base_input)
    summary_current = Summary.from_results(results_current)

    # Calculate with lower target spending
    input_with_target = base_input.model_copy(
        update={"post_fire_spending_per_month": 2500.0}
    )
    results_target = calculate_results_for_month(input_with_target)
    summary_target = Summary.from_results(results_target)

    # Both should reach FIRE
    assert summary_current is not None
    assert summary_target is not None

    # Target spending version should reach FIRE earlier
    assert summary_target.fire_age < summary_current.fire_age
    assert summary_target.years_till_fi < summary_current.years_till_fi


def test_post_fire_spending_inflation_adjusted() -> None:
    """Test that post_fire_spending is adjusted for inflation over time."""
    input_data = InputData(
        growth_rate=7.0,
        current_nw=100000.0,
        spending_per_month=3000.0,
        inflation=2.0,
        annual_salary_increase=3.0,
        income_per_month=6000.0,
        extra_income=0.0,
        date_of_birth=datetime.date(1990, 1, 1),
        safe_withdraw_rate=4.0,
        post_fire_spending_per_month=2000.0,
    )

    results = calculate_results_for_month(input_data, target=12)

    # Check that post_fire_spending increases with inflation
    first = results[0]
    last = results[-1]

    assert first.post_fire_spending == 2000.0
    # After 12 months with 2% annual inflation, target should increase
    expected_target_after_12_months = 2000.0 * (input_data.monthly_inflation**12)
    assert abs(last.post_fire_spending - expected_target_after_12_months) < 0.01
