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
    plot_age_vs_monthly_safe_withdraw,
    plot_age_vs_net_worth,
    plot_savings_vs_spending,
)

FOLDER = Path(__file__).parent.resolve()


app = FastAPI()
app.mount("/static", StaticFiles(directory=FOLDER / "static"), name="static")
templates = Jinja2Templates(directory=FOLDER / "templates")
htmx_init(templates=templates)


@app.get("/", response_class=HTMLResponse)
@htmx("index.html", "index.html")
async def index(
    request: Request,
    # Default values for the input fields
    growth_rate: Optional[float] = 7,
    current_nw: Optional[float] = 50_000,
    spending_per_month: Optional[float] = 4_000,
    inflation: Optional[float] = 2,
    annual_salary_increase: Optional[float] = 5,
    income_per_month: Optional[float] = 8_000,
    extra_income: Optional[float] = 0,
    date_of_birth: Optional[str] = "1990-01-01",
    safe_withdraw_rate: Optional[float] = 4,
    extra_spending: Optional[float] = 0,
    change_dates: list[str] = [],
    change_fields: list[str] = [],
    change_values: list[str] = [],
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
    growth_rate: float = Query(...),
    current_nw: float = Query(...),
    spending_per_month: float = Query(...),
    inflation: float = Query(...),
    annual_salary_increase: float = Query(...),
    income_per_month: float = Query(...),
    extra_income: float = Query(...),
    date_of_birth: str = Query(...),
    safe_withdraw_rate: float = Query(...),
    extra_spending: float = Query(...),
    change_dates: list[str] = Query([]),
    change_fields: list[str] = Query([]),
    change_values: list[str] = Query([]),
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
    input_data_with_extra = input_data.copy(
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
        age_vs_monthly_safe_withdraw_plot = plot_age_vs_monthly_safe_withdraw(
            results, summary
        )
        savings_vs_spending_plot = plot_savings_vs_spending(results, summary)
    else:
        age_vs_net_worth_plot = None
        age_vs_monthly_safe_withdraw_plot = None
        savings_vs_spending_plot = None

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
        "age_vs_monthly_safe_withdraw_plot": age_vs_monthly_safe_withdraw_plot,
        "savings_vs_spending_plot": savings_vs_spending_plot,
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
