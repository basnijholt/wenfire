from .fire import Results, Summary

_PLOT_PROPERTIES = dict(width=360, usermeta={"embedOptions": {"actions": False}})


def _format_time_from_now(years: float) -> str:
    """Format years from now into readable text."""
    if years < 0.1:
        return "now"
    else:
        return f"{years:.1f} yr from now"


def plot_age_vs_net_worth(results: list[Results], summary: Summary):
    """Generate data for ApexCharts net worth chart."""
    # Prepare data for each series using dates instead of ages
    current_date = results[0].input_data.now

    net_worth_data = [
        {
            "x": result.date.isoformat(),
            "y": result.nw,
            "age": result.age,
            "time_from_now": (result.date - current_date).days / 365.25,
            "time_from_now_text": _format_time_from_now(
                (result.date - current_date).days / 365.25
            ),
        }
        for result in results
    ]
    saved_data = [
        {
            "x": result.date.isoformat(),
            "y": result.total_saved,
            "age": result.age,
            "time_from_now": (result.date - current_date).days / 365.25,
            "time_from_now_text": _format_time_from_now(
                (result.date - current_date).days / 365.25
            ),
        }
        for result in results
    ]
    profits_data = [
        {
            "x": result.date.isoformat(),
            "y": result.total_investment_profits,
            "age": result.age,
            "time_from_now": (result.date - current_date).days / 365.25,
            "time_from_now_text": _format_time_from_now(
                (result.date - current_date).days / 365.25
            ),
        }
        for result in results
    ]

    return {
        "series": [
            {"name": "Net Worth", "data": net_worth_data},
            {"name": "Saved", "data": saved_data},
            {"name": "Profits", "data": profits_data},
        ],
        "fire_age": summary.fire_age,
        "fire_date": summary.fire_date.isoformat(),
        "nw_at_fi": summary.nw_at_fi,
    }


def plot_age_vs_monthly_safe_withdraw(results: list[Results], summary: Summary):
    """Generate data for ApexCharts monthly safe withdrawal chart."""
    monthly_safe_withdraw_data = [
        {"x": result.date.isoformat(), "y": result.safe_withdraw_rule_monthly}
        for result in results
    ]
    spending_data = [
        {"x": result.date.isoformat(), "y": result.spending} for result in results
    ]
    income_data = [
        {"x": result.date.isoformat(), "y": result.income} for result in results
    ]

    return {
        "series": [
            {"name": "Monthly Safe Withdraw", "data": monthly_safe_withdraw_data},
            {"name": "Spending", "data": spending_data},
            {"name": "Income", "data": income_data},
        ],
        "fire_age": summary.fire_age,
        "fire_date": summary.fire_date.isoformat(),
        "spending_at_fi": summary.spending_at_fi,
    }


def plot_savings_vs_spending(results: list[Results], summary: Summary):
    """Generate data for ApexCharts savings vs spending chart."""
    savings_data = [
        {"x": result.date.isoformat(), "y": result.saving} for result in results
    ]
    spending_data = [
        {"x": result.date.isoformat(), "y": result.spending} for result in results
    ]
    investment_profits_data = [
        {"x": result.date.isoformat(), "y": result.investment_profits}
        for result in results
    ]

    return {
        "series": [
            {"name": "Savings", "data": savings_data},
            {"name": "Spending", "data": spending_data},
            {"name": "Investment Profits", "data": investment_profits_data},
        ],
        "fire_age": summary.fire_age,
        "fire_date": summary.fire_date.isoformat(),
        "saving_at_fi": summary.saving_at_fi,
        "spending_at_fi": summary.spending_at_fi,
    }


def plot_monthly_financial_flows(results: list[Results], summary: Summary):
    """Generate data for ApexCharts comprehensive monthly financial flows chart."""
    current_date = results[0].input_data.now

    monthly_safe_withdraw_data = [
        {
            "x": result.date.isoformat(),
            "y": result.safe_withdraw_rule_monthly,
            "age": result.age,
            "time_from_now": (result.date - current_date).days / 365.25,
            "time_from_now_text": _format_time_from_now(
                (result.date - current_date).days / 365.25
            ),
        }
        for result in results
    ]
    spending_data = [
        {
            "x": result.date.isoformat(),
            "y": result.spending,
            "age": result.age,
            "time_from_now": (result.date - current_date).days / 365.25,
            "time_from_now_text": _format_time_from_now(
                (result.date - current_date).days / 365.25
            ),
        }
        for result in results
    ]
    income_data = [
        {
            "x": result.date.isoformat(),
            "y": result.income,
            "age": result.age,
            "time_from_now": (result.date - current_date).days / 365.25,
            "time_from_now_text": _format_time_from_now(
                (result.date - current_date).days / 365.25
            ),
        }
        for result in results
    ]
    savings_data = [
        {
            "x": result.date.isoformat(),
            "y": result.saving,
            "age": result.age,
            "time_from_now": (result.date - current_date).days / 365.25,
            "time_from_now_text": _format_time_from_now(
                (result.date - current_date).days / 365.25
            ),
        }
        for result in results
    ]
    investment_profits_data = [
        {
            "x": result.date.isoformat(),
            "y": result.investment_profits,
            "age": result.age,
            "time_from_now": (result.date - current_date).days / 365.25,
            "time_from_now_text": _format_time_from_now(
                (result.date - current_date).days / 365.25
            ),
        }
        for result in results
    ]

    return {
        "series": [
            {"name": "Monthly Safe Withdraw", "data": monthly_safe_withdraw_data},
            {"name": "Income", "data": income_data},
            {"name": "Spending", "data": spending_data},
            {"name": "Savings", "data": savings_data},
            {"name": "Investment Profits", "data": investment_profits_data},
        ],
        "fire_age": summary.fire_age,
        "fire_date": summary.fire_date.isoformat(),
        "spending_at_fi": summary.spending_at_fi,
        "saving_at_fi": summary.saving_at_fi,
    }
