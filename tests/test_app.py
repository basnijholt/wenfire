# test_financial.py

import datetime
from unittest.mock import patch

import pytest
from dateutil.relativedelta import relativedelta

from pydantic import ValidationError

from wenfire.fire import (
    InputData,
    Results,
    Summary,
    calculate_results_for_month,
    interpolate,
    retirement_index,
)

# For demonstration, I'll assume the classes are available in the current namespace.


# Fixtures
@pytest.fixture
def input_data():
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
@pytest.fixture
def fixed_today():
    return datetime.date(2024, 4, 1)


# Tests for InputData
def test_input_data_age_at(input_data, fixed_today):
    target_date = datetime.date(2024, 4, 1)
    with patch("datetime.date") as mock_date:
        mock_date.today.return_value = fixed_today
        mock_date.side_effect = lambda *args, **kw: datetime.date(*args, **kw)
        age = input_data.age_at(target_date)
        expected_age = 34.25  # From 1990-01-01 to 2024-04-01
        assert abs(age - expected_age) < 0.01, f"Expected age {expected_age}, got {age}"


def test_input_data_age(input_data, fixed_today):
    with patch("datetime.date") as mock_date:
        mock_date.today.return_value = fixed_today
        mock_date.side_effect = lambda *args, **kw: datetime.date(*args, **kw)
        age = input_data.age
        expected_age = 34.25  # From 1990-01-01 to 2024-04-01
        assert abs(age - expected_age) < 0.01, f"Expected age {expected_age}, got {age}"


def test_input_data_saving_per_month(input_data):
    expected_saving = (
        input_data.income_per_month
        + input_data.extra_income
        - input_data.spending_per_month
    )
    assert (
        input_data.saving_per_month == expected_saving
    ), "Incorrect saving_per_month calculation"


def test_input_data_monthly_growth_rate(input_data):
    expected = (1 + input_data.growth_rate / 100) ** (1 / 12)
    assert (
        abs(input_data.monthly_growth_rate - expected) < 1e-6
    ), "Incorrect monthly_growth_rate calculation"


def test_input_data_monthly_inflation(input_data):
    expected = (1 + input_data.inflation / 100) ** (1 / 12)
    assert (
        abs(input_data.monthly_inflation - expected) < 1e-6
    ), "Incorrect monthly_inflation calculation"


def test_input_data_monthly_salary_increase_rate(input_data):
    expected = (1 + input_data.annual_salary_increase / 100) ** (1 / 12)
    assert (
        abs(input_data.monthly_salary_increase_rate - expected) < 1e-6
    ), "Incorrect monthly_salary_increase_rate calculation"


# Tests for Results
def test_results_initial(input_data):
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


def test_results_next_month(input_data, fixed_today):
    with patch("datetime.date") as mock_date:
        mock_date.today.return_value = fixed_today
        mock_date.side_effect = lambda *args, **kw: datetime.date(*args, **kw)
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
def test_retirement_index():
    input_data = InputData(
        growth_rate=5.0,
        current_nw=100000.0,
        spending_per_month=3000.0,
        inflation=2.0,
        annual_salary_increase=3.0,
        income_per_month=5000.0,
        extra_income=500.0,
        date_of_birth=datetime.date(1990, 1, 1),
    )
    r1 = Results(
        months=0,
        nw=100000.0,
        income=5000.0,
        extra_income=500.0,
        spending=3000.0,
        delta_nw=0.0,
        total_saved=100000.0,
        input_data=input_data,
    )
    r2 = Results(
        months=1,
        nw=102000.0,
        income=5000.0,
        extra_income=500.0,
        spending=3000.0,
        delta_nw=2000.0,
        total_saved=102000.0,
        input_data=input_data,
    )
    results = [r1, r2]
    index = retirement_index(results)
    assert index == 1, f"Expected retirement index 1, got {index}"

    # Test when no retirement condition met
    results = [r1]
    index = retirement_index(results)
    assert index is None, "Expected retirement index None when condition not met"


def test_interpolate():
    assert interpolate(0, 10, 0.5) == 5.0, "Interpolation failed for middle fraction"
    assert (
        interpolate(10, 20, 0.25) == 12.5
    ), "Interpolation failed for quarter fraction"
    assert interpolate(-5, 5, 0.5) == 0.0, "Interpolation failed with negative numbers"
    assert interpolate(100, 200, 0) == 100, "Interpolation failed for fraction 0"
    assert interpolate(100, 200, 1) == 200, "Interpolation failed for fraction 1"


# Tests for Summary
def test_summary_from_results(input_data, fixed_today):
    with patch("datetime.date") as mock_date:
        mock_date.today.return_value = fixed_today
        mock_date.side_effect = lambda *args, **kw: datetime.date(*args, **kw)

        # Create a list of Results where the retirement condition is met at month 2
        r0 = Results(
            months=0,
            nw=100000.0,
            income=5000.0,
            extra_income=500.0,
            spending=3000.0,
            delta_nw=0.0,
            total_saved=100000.0,
            input_data=input_data,
        )
        r1 = r0.next_month()
        r2 = r1.next_month()
        results = [r0, r1, r2]

        summary = Summary.from_results(results)
        assert (
            summary is not None
        ), "Summary should not be None when retirement condition is met"
        assert summary.months == r2.months
        assert summary.nw == r2.nw
        assert summary.income == r2.income
        assert summary.spending == r2.spending
        assert summary.age == input_data.age_at(summary.fire_date)
        assert summary.fire_age == summary.age
        assert summary.years_till_fi == summary.months / 12
        assert summary.safe_withdraw_at_fi == r2.safe_withdraw_rule_monthly
        assert summary.saving_at_fi == r2.saving
        assert summary.nw_at_fi == r2.nw
        assert summary.total_investment_profits == r2.total_investment_profits
        assert summary.total_saved == r2.total_saved


def test_summary_from_results_no_retirement(input_data):
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
def test_calculate_results_for_month_no_target(input_data, fixed_today):
    with patch("datetime.date") as mock_date:
        mock_date.today.return_value = fixed_today
        mock_date.side_effect = lambda *args, **kw: datetime.date(*args, **kw)

        results = calculate_results_for_month(input_data)
        assert len(results) > 0, "Results should not be empty"
        # Check first result
        first = results[0]
        assert first.months == 0
        assert first.nw == input_data.current_nw
        assert first.income == input_data.income_per_month
        assert first.spending == input_data.spending_per_month


def test_calculate_results_for_month_with_target_date(input_data, fixed_today):
    target_date = fixed_today + relativedelta(months=12)
    results = calculate_results_for_month(input_data, target=target_date)
    assert len(results) == 13, f"Expected 13 months, got {len(results)}"


def test_calculate_results_for_month_with_target_int(input_data):
    target_months = 24
    results = calculate_results_for_month(input_data, target=target_months)
    assert len(results) == 25, f"Expected 25 months, got {len(results)}"


def test_calculate_results_for_month_retirement_condition(input_data, fixed_today):
    # Modify input_data to meet retirement condition quickly
    input_data.spending_per_month = 4000.0  # Increase spending
    input_data.extra_income = 2000.0  # Increase extra income to make saving high

    results = calculate_results_for_month(input_data)
    # Expect retirement condition met early
    assert len(results) < 100 * 12, "Retirement condition should have been met early"


# Tests for Validation
def test_input_data_validation():
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


def test_results_validation(input_data):
    with pytest.raises(ValidationError):
        Results(
            months=-1,  # Invalid negative months
            nw=-1000.0,  # Invalid negative net worth
            income=5000.0,
            extra_income=500.0,
            spending=3000.0,
            delta_nw=1000.0,
            total_saved=100000.0,
            input_data=input_data,
        )


# Additional edge case tests
def test_age_at_leap_year(input_data, fixed_today):
    birth_date = datetime.date(2000, 2, 29)
    input_data.date_of_birth = birth_date
    target_date = datetime.date(2024, 2, 28)
    age = input_data.age_at(target_date)
    expected_age = 23.99726  # Approximately, not reaching the 24th birthday
    assert abs(age - expected_age) < 0.01, f"Expected age {expected_age}, got {age}"


def test_interpolate_fraction_out_of_bounds():
    # Even though the function does not restrict fraction, test behavior
    assert (
        interpolate(0, 10, -0.5) == -5.0
    ), "Interpolation failed for negative fraction"
    assert interpolate(0, 10, 1.5) == 15.0, "Interpolation failed for fraction >1"


def test_retirement_index_multiple_meets():
    input_data = InputData(
        growth_rate=5.0,
        current_nw=50000.0,
        spending_per_month=2000.0,
        inflation=2.0,
        annual_salary_increase=3.0,
        income_per_month=6000.0,
        extra_income=1000.0,
        date_of_birth=datetime.date(1985, 6, 15),
    )
    r1 = Results(
        months=0,
        nw=50000.0,
        income=6000.0,
        extra_income=1000.0,
        spending=2000.0,
        delta_nw=0.0,
        total_saved=50000.0,
        input_data=input_data,
    )
    # Simulate multiple retirement condition meets
    r2 = Results(
        months=1,
        nw=55000.0,
        income=6000.0,
        extra_income=1000.0,
        spending=2000.0,
        delta_nw=5000.0,
        total_saved=55000.0,
        input_data=input_data,
    )
    r3 = Results(
        months=2,
        nw=60500.0,
        income=6000.0,
        extra_income=1000.0,
        spending=2000.0,
        delta_nw=5500.0,
        total_saved=60500.0,
        input_data=input_data,
    )
    results = [r1, r2, r3]
    index = retirement_index(results)
    assert index == 1, f"Expected first retirement index 1, got {index}"


def test_summary_safe_withdraw_at_age():
    input_data = InputData(
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
    r = Results(
        months=120,  # 10 years
        nw=200000.0,
        income=8000.0,
        extra_income=500.0,
        spending=3500.0,
        delta_nw=1000.0,
        total_saved=200000.0,
        input_data=input_data,
    )
    results = [r]
    summary = Summary.from_results(results)
    assert summary is not None
    assert len(summary.safe_withdraw_at_age) == 1
    expected_age = input_data.age_at(r.date)
    expected_key = round(expected_age)
    expected_value = r.safe_withdraw_rule_yearly / 12
    assert (
        summary.safe_withdraw_at_age.get(expected_key) == expected_value
    ), "Incorrect safe_withdraw_at_age"
