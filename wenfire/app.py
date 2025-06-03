from __future__ import annotations

import datetime
import uuid
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_htmx import htmx, htmx_init

from .fire import InputData, ParameterChange, Summary, calculate_results_for_month
from .plots import (
    plot_age_vs_net_worth,
    plot_monthly_financial_flows,
)

FOLDER = Path(__file__).parent.resolve()


app = FastAPI()
app.mount("/static", StaticFiles(directory=FOLDER / "static"), name="static")
templates = Jinja2Templates(directory=FOLDER / "templates")
htmx_init(templates=templates)

# Default values for the input fields
DEFAULT_GROWTH_RATE = 7
DEFAULT_CURRENT_NW = 50_000
DEFAULT_SPENDING_PER_MONTH = 4_000
DEFAULT_INFLATION = 2
DEFAULT_ANNUAL_SALARY_INCREASE = 5
DEFAULT_INCOME_PER_MONTH = 8_000
DEFAULT_EXTRA_INCOME = 0
DEFAULT_DATE_OF_BIRTH = "1990-01-01"
DEFAULT_SAFE_WITHDRAW_RATE = 4
DEFAULT_EXTRA_SPENDING = 0


@app.get("/", response_class=HTMLResponse)
@htmx("index.html", "index.html")
async def index(
    request: Request,
    growth_rate: Optional[float] = DEFAULT_GROWTH_RATE,
    current_nw: Optional[float] = DEFAULT_CURRENT_NW,
    spending_per_month: Optional[float] = DEFAULT_SPENDING_PER_MONTH,
    inflation: Optional[float] = DEFAULT_INFLATION,
    annual_salary_increase: Optional[float] = DEFAULT_ANNUAL_SALARY_INCREASE,
    income_per_month: Optional[float] = DEFAULT_INCOME_PER_MONTH,
    extra_income: Optional[float] = DEFAULT_EXTRA_INCOME,
    date_of_birth: Optional[str] = DEFAULT_DATE_OF_BIRTH,
    safe_withdraw_rate: Optional[float] = DEFAULT_SAFE_WITHDRAW_RATE,
    extra_spending: Optional[float] = DEFAULT_EXTRA_SPENDING,
    change_dates: list[str] = Query(default=[]),
    change_fields: list[str] = Query(default=[]),
    change_values: list[str] = Query(default=[]),
):
    parameter_changes = _parameter_changes(change_dates, change_fields, change_values)
    return {
        "request": request,
        "growth_rate": growth_rate,
        "current_nw": current_nw,
        "spending_per_month": spending_per_month,
        "inflation": inflation,
        "annual_salary_increase": annual_salary_increase,
        "income_per_month": income_per_month,
        "extra_income": extra_income,
        "date_of_birth": date_of_birth,
        "safe_withdraw_rate": safe_withdraw_rate,
        "extra_spending": extra_spending,
        "parameter_changes": parameter_changes,
    }


@app.get("/add-parameter-change", response_class=HTMLResponse)
async def add_parameter_change(request: Request):
    unique_id = uuid.uuid4().hex[:8]  # Generate a unique identifier
    return templates.TemplateResponse(
        "parameter_change.html.jinja2", {"request": request, "uuid": unique_id}
    )


@app.delete("/remove-parameter-change", response_class=HTMLResponse)
async def remove_parameter_change():
    # Since htmx handles the removal on the client side using hx-target and hx-swap,
    # the server doesn't need to perform any action. Just return an empty response.
    return Response("", status_code=200)


def format_currency(value):
    return "${:,.0f}".format(value).replace(",", ".")


def interpolate_color(
    x: float,
    x_red: int = -2000,
    x_orange: int = -1000,
    x_yellow: int = 0,
    x_light_green: int = 1000,
    x_green: int = 2000,
    return_hex: bool = True,
):
    color_points = {
        x_red: (255, 0, 0),
        x_orange: (255, 167, 0),
        x_yellow: (255, 244, 0),
        x_light_green: (163, 255, 0),
        x_green: (44, 186, 0),
    }

    def _interpolate_color(c1, c2, ratio):
        return tuple(int(c1[i] + (c2[i] - c1[i]) * ratio) for i in range(3))

    if x <= x_red:
        rgb = color_points[x_red]
        return _rgb_to_hex(rgb) if return_hex else rgb

    elif x >= x_green:
        rgb = color_points[x_green]
        return _rgb_to_hex(rgb) if return_hex else rgb
    else:
        sorted_keys = sorted(color_points.keys())
        for i, key in enumerate(sorted_keys[:-1]):
            if key <= x < sorted_keys[i + 1]:
                c1 = color_points[key]
                c2 = color_points[sorted_keys[i + 1]]
                ratio = (x - key) / (sorted_keys[i + 1] - key)
                rgb = _interpolate_color(c1, c2, ratio)
                return _rgb_to_hex(rgb) if return_hex else rgb


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def _date_str_to_date(date_str: str) -> datetime.date:
    return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()


def _parameter_changes(
    change_dates: list[str],
    change_fields: list[str],
    change_values: list[str],
) -> list[ParameterChange]:
    parameter_changes = []
    for date, field, value in zip(change_dates, change_fields, change_values):
        date_ = _date_str_to_date(date)
        parameter_changes.append(ParameterChange(date=date_, field=field, value=value))
    return sorted(parameter_changes, key=lambda x: x.date)


@app.get("/calculate", response_class=HTMLResponse)
@htmx("results_partial.html", "index.html")
async def calculate(
    request: Request,
    growth_rate: float = Query(default=DEFAULT_GROWTH_RATE),
    current_nw: float = Query(default=DEFAULT_CURRENT_NW),
    spending_per_month: float = Query(default=DEFAULT_SPENDING_PER_MONTH),
    inflation: float = Query(default=DEFAULT_INFLATION),
    annual_salary_increase: float = Query(default=DEFAULT_ANNUAL_SALARY_INCREASE),
    income_per_month: float = Query(default=DEFAULT_INCOME_PER_MONTH),
    extra_income: float = Query(default=DEFAULT_EXTRA_INCOME),
    date_of_birth: str = Query(default=DEFAULT_DATE_OF_BIRTH),
    safe_withdraw_rate: float = Query(default=DEFAULT_SAFE_WITHDRAW_RATE),
    extra_spending: float = Query(default=DEFAULT_EXTRA_SPENDING),
    change_dates: list[str] = Query(default=[]),
    change_fields: list[str] = Query(default=[]),
    change_values: list[str] = Query(default=[]),
):
    parameter_changes = _parameter_changes(change_dates, change_fields, change_values)
    dob = _date_str_to_date(date_of_birth)
    input_data = InputData(
        growth_rate=growth_rate,
        current_nw=current_nw,
        spending_per_month=spending_per_month,
        inflation=inflation,
        annual_salary_increase=annual_salary_increase,
        income_per_month=income_per_month,
        extra_income=extra_income,
        date_of_birth=dob,
        safe_withdraw_rate=safe_withdraw_rate,
        parameter_changes=parameter_changes,
    )
    input_data_with_extra = input_data.model_copy(
        update={"current_nw": current_nw - extra_spending}
    )

    # Calculate results without extra spending (main results)
    results = calculate_results_for_month(input_data)
    summary = Summary.from_results(results)

    # Calculate results with extra spending only for comparison
    results_with_extra = calculate_results_for_month(input_data_with_extra)
    summary_with_extra = Summary.from_results(results_with_extra)

    time_difference = None
    if summary and summary_with_extra:
        time_difference = (
            summary_with_extra.fire_date - summary.fire_date
        ).total_seconds() / (365.25 * 24 * 3600)

    if summary is not None:
        age_vs_net_worth_plot = plot_age_vs_net_worth(results, summary)
        monthly_financial_flows_plot = plot_monthly_financial_flows(results, summary)
    else:
        age_vs_net_worth_plot = None
        monthly_financial_flows_plot = None

    # Create URL parameters string
    url_params = urlencode(
        {
            "growth_rate": growth_rate,
            "current_nw": current_nw,
            "spending_per_month": spending_per_month,
            "inflation": inflation,
            "annual_salary_increase": annual_salary_increase,
            "income_per_month": income_per_month,
            "extra_income": extra_income,
            "date_of_birth": date_of_birth,
            "safe_withdraw_rate": safe_withdraw_rate,
            "extra_spending": extra_spending,
            "change_dates": change_dates,
            "change_fields": change_fields,
            "change_values": change_values,
        }
    )

    context = {
        "request": request,
        "results": results,
        "summary": summary,
        "growth_rate": growth_rate,
        "current_nw": current_nw,
        "spending_per_month": spending_per_month,
        "inflation": inflation,
        "annual_salary_increase": annual_salary_increase,
        "income_per_month": income_per_month,
        "extra_income": extra_income,
        "date_of_birth": dob.strftime("%Y-%m-%d"),
        "safe_withdraw_rate": safe_withdraw_rate,
        "extra_spending": extra_spending,
        "parameter_changes": parameter_changes,
        "age_vs_net_worth_plot": age_vs_net_worth_plot,
        "monthly_financial_flows_plot": monthly_financial_flows_plot,
        "format_currency": format_currency,
        "interpolate_color": interpolate_color,
        "time_difference": time_difference,
        "summary_with_extra": summary_with_extra,
        "url_params": url_params,
    }

    return context


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, log_level="info", reload=True)
