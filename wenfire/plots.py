from .fire import Results, Summary
from datetime import datetime

_PLOT_PROPERTIES = dict(width=360, usermeta={"embedOptions": {"actions": False}})


def _format_time_from_now(years: float) -> str:
    """Format years from now into readable text."""
    if years < 0.1:
        return "now"
    else:
        return f"{years:.1f} yr"


def _create_data_point(result, current_date, y_field: str):
    """Create a standardized data point with date, y-value, age, and time info."""
    time_years = (result.date - current_date).days / 365.25
    return {
        "x": result.date.isoformat(),
        "y": getattr(result, y_field),
        "age": result.age,
        "time_from_now": time_years,
        "time_from_now_text": _format_time_from_now(time_years),
    }


def _get_theme_colors(theme: str = "light") -> dict:
    """Get theme-appropriate colors for charts."""
    if theme == "dark":
        return {
            "background": "#2c2c2c",
            "foreground": "#ecf0f1",
            "gridColor": "#404040",
            "tooltipBg": "#404040",
            "tooltipColor": "#ecf0f1",
        }
    else:
        return {
            "background": "#ffffff",
            "foreground": "#2c3e50",
            "gridColor": "#e9ecef",
            "tooltipBg": "#ffffff",
            "tooltipColor": "#2c3e50",
        }


def _create_base_chart_config(
    chart_data: dict, y_axis_title: str, theme: str = "light"
) -> dict:
    """Create base ApexCharts configuration with theme support."""
    colors = _get_theme_colors(theme)

    config = {
        "series": chart_data["series"],
        "chart": {
            "type": "area",
            "stacked": False,
            "height": 350,
            "background": colors["background"],
            "foreColor": colors["foreground"],
            "zoom": {"type": "x", "enabled": True, "autoScaleYaxis": True},
            "toolbar": {"show": False},
            "animations": {"enabled": True, "easing": "easeinout", "speed": 800},
        },
        "dataLabels": {"enabled": False},
        "markers": {"size": 0},
        "fill": {
            "type": "gradient",
            "gradient": {
                "shadeIntensity": 1,
                "inverseColors": False,
                "opacityFrom": 0.5,
                "opacityTo": 0,
                "stops": [0, 90, 100],
            },
        },
        "colors": ["#ff6b35", "#6c5ce7", "#00b894", "#e17055", "#0984e3"],
        "stroke": {"curve": "smooth", "width": 2},
        "grid": {
            "borderColor": colors["gridColor"],
            "strokeDashArray": 0,
            "xaxis": {"lines": {"show": True}},
            "yaxis": {"lines": {"show": True}},
        },
        "xaxis": {
            "type": "datetime",
            "title": {"text": "Date", "style": {"color": colors["foreground"]}},
            "labels": {"style": {"colors": colors["foreground"]}},
        },
        "yaxis": {
            "title": {"text": y_axis_title, "style": {"color": colors["foreground"]}},
            "labels": {"style": {"colors": colors["foreground"]}},
        },
        "tooltip": {
            "theme": theme,
            "shared": True,
            "style": {"fontSize": "12px", "color": colors["tooltipColor"]},
        },
        "legend": {
            "position": "top",
            "horizontalAlign": "left",
            "labels": {"colors": colors["foreground"]},
        },
    }

    # Add FIRE date annotation if available
    if chart_data.get("fire_date"):
        # Convert ISO date string to timestamp (milliseconds since epoch) for ApexCharts
        fire_date_dt = datetime.fromisoformat(chart_data["fire_date"])
        fire_date_timestamp = int(fire_date_dt.timestamp() * 1000)

        config["annotations"] = {
            "xaxis": [
                {
                    "x": fire_date_timestamp,
                    "borderColor": colors["foreground"],
                    "strokeDashArray": 5,
                    "label": {
                        "text": "FIRE Date",
                        "style": {
                            "color": colors["foreground"],
                            "background": colors["background"],
                        },
                    },
                }
            ]
        }

    return config


def plot_age_vs_net_worth(results: list[Results], summary: Summary):
    """Generate complete ApexCharts configuration for net worth chart."""
    current_date = results[0].input_data.now

    # Create data series using the helper function
    series_data = [
        ("Net Worth", "nw"),
        ("Saved", "total_saved"),
        ("Profits", "total_investment_profits"),
    ]

    series = []
    for name, field in series_data:
        data = [_create_data_point(result, current_date, field) for result in results]
        series.append({"name": name, "data": data})

    chart_data = {
        "series": series,
        "fire_date": summary.fire_date.isoformat(),
    }

    return {
        "config_light": _create_base_chart_config(chart_data, "Amount ($)", "light"),
        "config_dark": _create_base_chart_config(chart_data, "Amount ($)", "dark"),
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
    """Generate complete ApexCharts configuration for monthly financial flows chart."""
    current_date = results[0].input_data.now

    # Create data series using the helper function
    # Use actual_spending which switches to post-FIRE spending after FIRE is reached
    series_data = [
        ("Monthly Safe Withdraw", "safe_withdraw_rule_monthly"),
        ("Income", "income"),
        ("Spending", "actual_spending"),
        ("Savings", "saving"),
        ("Investment Profits", "investment_profits"),
    ]

    series = []
    for name, field in series_data:
        data = [_create_data_point(result, current_date, field) for result in results]
        series.append({"name": name, "data": data})

    chart_data = {
        "series": series,
        "fire_date": summary.fire_date.isoformat(),
    }

    return {
        "config_light": _create_base_chart_config(
            chart_data, "Monthly Amount ($)", "light"
        ),
        "config_dark": _create_base_chart_config(
            chart_data, "Monthly Amount ($)", "dark"
        ),
    }
