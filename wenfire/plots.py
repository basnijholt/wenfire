from .fire import Results, Summary

_PLOT_PROPERTIES = dict(width=360, usermeta={"embedOptions": {"actions": False}})


def plot_age_vs_net_worth(results: list[Results], summary: Summary):
    """Generate data for ApexCharts net worth chart."""
    # Prepare data for each series
    net_worth_data = [{"x": result.age, "y": result.nw} for result in results]
    saved_data = [{"x": result.age, "y": result.total_saved} for result in results]
    profits_data = [
        {"x": result.age, "y": result.total_investment_profits} for result in results
    ]

    return {
        "series": [
            {"name": "Net Worth", "data": net_worth_data},
            {"name": "Saved", "data": saved_data},
            {"name": "Profits", "data": profits_data},
        ],
        "fire_age": summary.fire_age,
        "nw_at_fi": summary.nw_at_fi,
    }


def plot_age_vs_monthly_safe_withdraw(results: list[Results], summary: Summary):
    """Generate data for ApexCharts monthly safe withdrawal chart."""
    monthly_safe_withdraw_data = [
        {"x": result.age, "y": result.safe_withdraw_rule_monthly} for result in results
    ]
    spending_data = [{"x": result.age, "y": result.spending} for result in results]
    income_data = [{"x": result.age, "y": result.income} for result in results]

    return {
        "series": [
            {"name": "Monthly Safe Withdraw", "data": monthly_safe_withdraw_data},
            {"name": "Spending", "data": spending_data},
            {"name": "Income", "data": income_data},
        ],
        "fire_age": summary.fire_age,
        "spending_at_fi": summary.spending_at_fi,
    }


def plot_savings_vs_spending(results: list[Results], summary: Summary):
    """Generate data for ApexCharts savings vs spending chart."""
    savings_data = [{"x": result.age, "y": result.saving} for result in results]
    spending_data = [{"x": result.age, "y": result.spending} for result in results]
    investment_profits_data = [
        {"x": result.age, "y": result.investment_profits} for result in results
    ]

    return {
        "series": [
            {"name": "Savings", "data": savings_data},
            {"name": "Spending", "data": spending_data},
            {"name": "Investment Profits", "data": investment_profits_data},
        ],
        "fire_age": summary.fire_age,
        "saving_at_fi": summary.saving_at_fi,
        "spending_at_fi": summary.spending_at_fi,
    }
