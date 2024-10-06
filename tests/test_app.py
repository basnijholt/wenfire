from fastapi.testclient import TestClient
from app import app

client = TestClient(app)


def test_index():
    response = client.get("/")
    assert response.status_code == 200
    assert "WenFire" in response.text


def test_calculate_no_changes():
    response = client.post(
        "/calculate",
        data={
            "growth_rate": "7",
            "current_nw": "50000",
            "spending_per_month": "4000",
            "inflation": "2",
            "annual_salary_increase": "5",
            "income_per_month": "8000",
            "extra_income": "0",
            "date_of_birth": "1990-01-01",
            "safe_withdraw_rate": "4",
            "extra_spending": "0",
        },
    )
    assert response.status_code == 200
    assert "Retirement Age" in response.text


def test_calculate_with_changes():
    response = client.post(
        "/calculate",
        data={
            "growth_rate": "7",
            "current_nw": "50000",
            "spending_per_month": "4000",
            "inflation": "2",
            "annual_salary_increase": "5",
            "income_per_month": "8000",
            "extra_income": "0",
            "date_of_birth": "1990-01-01",
            "safe_withdraw_rate": "4",
            "extra_spending": "0",
            "change_dates": ["2025-01-01", "2030-01-01"],
            "change_growth_rates": ["8", "9"],
            "change_spending_per_months": ["3500", "3000"],
            "change_inflations": ["2.5", "3"],
            "change_annual_salary_increases": ["6", "7"],
            "change_income_per_months": ["8500", "9000"],
            "change_extra_incomes": ["500", "1000"],
        },
    )
    assert response.status_code == 200
    assert "Retirement Age" in response.text


def test_calculate_invalid_date():
    response = client.post(
        "/calculate",
        data={
            "growth_rate": "7",
            "current_nw": "50000",
            "spending_per_month": "4000",
            "inflation": "2",
            "annual_salary_increase": "5",
            "income_per_month": "8000",
            "extra_income": "0",
            "date_of_birth": "invalid-date",
            "safe_withdraw_rate": "4",
            "extra_spending": "0",
        },
    )
    assert response.status_code == 422  # Unprocessable Entity


def test_calculate_missing_fields():
    response = client.post(
        "/calculate",
        data={
            "growth_rate": "7",
            "current_nw": "50000",
            # Missing 'spending_per_month'
            "inflation": "2",
            "annual_salary_increase": "5",
            "income_per_month": "8000",
            "extra_income": "0",
            "date_of_birth": "1990-01-01",
            "safe_withdraw_rate": "4",
            "extra_spending": "0",
        },
    )
    assert response.status_code == 422  # Unprocessable Entity


def test_calculate_negative_values():
    response = client.post(
        "/calculate",
        data={
            "growth_rate": "-7",
            "current_nw": "-50000",
            "spending_per_month": "-4000",
            "inflation": "-2",
            "annual_salary_increase": "-5",
            "income_per_month": "-8000",
            "extra_income": "-500",
            "date_of_birth": "1990-01-01",
            "safe_withdraw_rate": "-4",
            "extra_spending": "-1000",
        },
    )
    assert response.status_code == 200
    assert "Retirement Age" in response.text


def test_calculate_large_numbers():
    response = client.post(
        "/calculate",
        data={
            "growth_rate": "1000",
            "current_nw": "1000000000",
            "spending_per_month": "10000000",
            "inflation": "100",
            "annual_salary_increase": "100",
            "income_per_month": "10000000",
            "extra_income": "1000000",
            "date_of_birth": "1990-01-01",
            "safe_withdraw_rate": "100",
            "extra_spending": "100000000",
        },
    )
    assert response.status_code == 200
    assert "Retirement Age" in response.text


def test_calculate_zero_values():
    response = client.post(
        "/calculate",
        data={
            "growth_rate": "0",
            "current_nw": "0",
            "spending_per_month": "0",
            "inflation": "0",
            "annual_salary_increase": "0",
            "income_per_month": "0",
            "extra_income": "0",
            "date_of_birth": "1990-01-01",
            "safe_withdraw_rate": "0",
            "extra_spending": "0",
        },
    )
    assert response.status_code == 200
    assert "Retirement Age" in response.text


def test_calculate_future_dob():
    from datetime import datetime, timedelta

    future_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    response = client.post(
        "/calculate",
        data={
            "growth_rate": "7",
            "current_nw": "50000",
            "spending_per_month": "4000",
            "inflation": "2",
            "annual_salary_increase": "5",
            "income_per_month": "8000",
            "extra_income": "0",
            "date_of_birth": future_date,
            "safe_withdraw_rate": "4",
            "extra_spending": "0",
        },
    )
    assert response.status_code == 200
    assert "Retirement Age" in response.text
