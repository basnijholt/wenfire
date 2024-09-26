from __future__ import annotations

import datetime
from datetime import date
from pathlib import Path
from typing import Optional

import altair as alt
from dateutil.relativedelta import relativedelta
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from fastapi import Query
from fastapi_htmx import htmx, htmx_init
from urllib.parse import urlencode

_PLOT_PROPERTIES = dict(width=360, usermeta={"embedOptions": {"actions": False}})

FOLDER = Path(__file__).parent.resolve()


class InputData(BaseModel):
    growth_rate: float
    current_nw: float
    spending_per_month: float
    inflation: float
    annual_salary_increase: float
    income_per_month: float
    extra_income: float
    date_of_birth: datetime.date
    safe_withdraw_rate: float = 4

    @property
    def now(self):
        return datetime.date.today()

    def age_at(self, date) -> float:
        delta = relativedelta(date, self.date_of_birth)
        years = delta.years
        months = delta.months
        days = delta.days
        age_in_years = years + (months / 12) + (days / 365.25)
        return age_in_years

    @property
    def age(self) -> float:
        return self.age_at(self.now)

    @property
    def saving_per_month(self):
        return self.income_per_month + self.extra_income - self.spending_per_month

    @property
    def monthly_growth_rate(self):
        return (1 + self.growth_rate / 100) ** (1 / 12)

    @property
    def monthly_inflation(self):
        return (1 + self.inflation / 100) ** (1 / 12)

    @property
    def monthly_salary_increase_rate(self):
        return (1 + self.annual_salary_increase / 100) ** (1 / 12)


class Results(BaseModel):
    months: float
    nw: float
    income: float
    extra_income: float  # fixed extra income per month
    spending: float
    delta_nw: float
    total_saved: float
    input_data: InputData

    @property
    def date(self):
        return self.input_data.now + datetime.timedelta(days=365.25 / 12) * self.months

    @property
    def age(self):
        return self.input_data.age_at(self.date)

    @property
    def years(self) -> float:
        return self.months / 12

    @property
    def safe_withdraw_rule_monthly(self) -> float:
        return self.safe_withdraw_rule_yearly / 12

    @property
    def saving(self) -> float:
        return self.income + self.extra_income - self.spending

    @property
    def safe_withdraw_rule_yearly(self) -> float:
        return self.nw * self.input_data.safe_withdraw_rate / 100

    @property
    def safe_withdraw_minus_spending(self) -> float:
        return self.safe_withdraw_rule_monthly - self.spending

    @property
    def investment_profits(self) -> float:
        return self.nw * self.input_data.monthly_growth_rate - self.nw

    @property
    def total_investment_profits(self) -> float:
        return self.nw - self.total_saved

    def next_month(self) -> "Results":
        new_nw = self.nw + self.investment_profits + self.saving
        new_months = self.months + 1
        new_spending = self.spending * self.input_data.monthly_inflation
        new_income = self.income * self.input_data.monthly_salary_increase_rate
        new_delta_nw = new_nw - self.nw
        new_saved = self.total_saved + self.saving
        return Results(
            months=new_months,
            nw=new_nw,
            income=new_income,
            extra_income=self.extra_income,
            spending=new_spending,
            delta_nw=new_delta_nw,
            total_saved=new_saved,
            input_data=self.input_data,
        )


def retirement_index(results: list[Results]) -> int | None:
    for i, r in enumerate(results):
        if r.safe_withdraw_minus_spending >= 0:
            return i
    return None


def interpolate(start: float, end: float, fraction: float) -> float:
    return start + (end - start) * fraction


class Summary(BaseModel):
    age: float
    fire_age: float
    fire_date: date
    years_till_fi: float
    saving_at_fi: float
    safe_withdraw_at_fi: float
    spending_at_fi: float
    nw_at_fi: float
    total_investment_profits: float
    total_saved: float
    safe_withdraw_at_age: dict[int, float]

    @classmethod
    def _interpolate_result(cls, results: list[Results], index: int) -> Results:
        if index == 0:
            return results[index]

        last = results[index]
        second_last = results[index - 1]

        fraction = (0 - second_last.safe_withdraw_minus_spending) / (
            last.safe_withdraw_minus_spending - second_last.safe_withdraw_minus_spending
        )

        interpolated_months = interpolate(second_last.months, last.months, fraction)

        return Results(
            months=interpolated_months,
            nw=interpolate(second_last.nw, last.nw, fraction),
            income=interpolate(second_last.income, last.income, fraction),
            extra_income=second_last.extra_income,
            spending=interpolate(second_last.spending, last.spending, fraction),
            delta_nw=interpolate(second_last.delta_nw, last.delta_nw, fraction),
            total_saved=interpolate(
                second_last.total_saved, last.total_saved, fraction
            ),
            input_data=second_last.input_data,
        )

    @classmethod
    def from_results(cls, results: list[Results]) -> Summary | None:
        index = retirement_index(results)
        if index is None:
            return None

        r = cls._interpolate_result(results, index)

        safe_withdraw_at_age = {
            round(r.age): r.safe_withdraw_rule_yearly / 12
            for r in results
            if round(r.age, 1) % 1 == 0
        }
        return cls(
            age=r.input_data.age,
            fire_date=r.date,
            fire_age=r.age,
            years_till_fi=r.years,
            safe_withdraw_at_fi=r.safe_withdraw_rule_monthly,
            spending_at_fi=r.spending,
            saving_at_fi=r.saving,
            nw_at_fi=r.nw,
            total_investment_profits=r.total_investment_profits,
            total_saved=r.total_saved,
            safe_withdraw_at_age=safe_withdraw_at_age,
        )


app = FastAPI()
app.mount("/static", StaticFiles(directory=FOLDER / "static"), name="static")
templates = Jinja2Templates(directory=FOLDER / "templates")

# Initialize fastapi-htmx with your templates
htmx_init(templates=templates)


@app.get("/", response_class=HTMLResponse)
@htmx("index.html", "index.html")
async def index(
    request: Request,
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
):
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
    }


def calculate_results_for_month(
    data: InputData,
    target: int | date | None = None,
) -> list[Results]:
    # If target is a date, calculate the target month
    if isinstance(target, date):
        delta_months = (
            (target.year - data.now.year) * 12 + target.month - data.now.month
        )
    elif target is None:
        delta_months = 100 * 12
    else:
        delta_months = target

    # Set initial values
    r = Results(
        months=0,
        years=0,
        nw=data.current_nw,
        delta_nw=0,
        income=data.income_per_month,
        extra_income=data.extra_income,
        spending=data.spending_per_month,
        total_saved=data.current_nw,
        input_data=data,
    )
    results = [r]
    done_for = 0
    for _ in range(1, delta_months + 1):
        r = r.next_month()
        results.append(r)
        if r.safe_withdraw_minus_spending > 0:
            done_for += 1
            if done_for >= 24:
                break
    return results


def plot_age_vs_net_worth(results: list[Results], summary: Summary):
    data = [
        {
            "age": result.age,
            "net_worth": result.nw,
            "saved": result.total_saved,
            "profits": result.total_investment_profits,
        }
        for result in results
    ]

    base_chart = (
        alt.Chart(alt.Data(values=data))
        .transform_fold(["net_worth", "saved", "profits"], as_=["key", "value"])
        .mark_line()
        .encode(
            x=alt.X("age:Q", title="Age"),
            y=alt.Y("value:Q", title="Amount"),
            color=alt.Color(
                "key:N",
                title="Legend",
                scale=alt.Scale(
                    domain=["net_worth", "saved", "profits"],
                    range=["blue", "purple", "green"],
                ),
                legend=alt.Legend(orient="top-left"),
            ),
            tooltip=["key:N"],
        )
    )

    fire_age = summary.fire_age

    vertical_line = (
        alt.Chart(alt.Data(values=[{"fire_age": fire_age}]))
        .mark_rule(strokeDash=[5, 5], color="black")
        .encode(x="fire_age:Q")
    )

    horizontal_line = (
        alt.Chart(alt.Data(values=[{"spending_at_fi": summary.nw_at_fi}]))
        .mark_rule(strokeDash=[5, 5], color="black")
        .encode(y="spending_at_fi:Q")
    )
    chart = alt.layer(base_chart, vertical_line, horizontal_line).properties(
        **_PLOT_PROPERTIES
    )
    return chart.to_json()


def plot_age_vs_monthly_safe_withdraw(results: list[Results], summary: Summary):
    data = [
        {
            "age": result.age,
            "monthly_safe_withdraw": result.safe_withdraw_rule_monthly,
            "spending": result.spending,
        }
        for result in results
    ]

    base_chart = (
        alt.Chart(alt.Data(values=data))
        .transform_fold(["monthly_safe_withdraw", "spending"], as_=["key", "value"])
        .mark_line()
        .encode(
            x=alt.X("age:Q", title="Age"),
            y=alt.Y("value:Q", title="Montly Amount"),
            color=alt.Color(
                "key:N",
                title="Legend",
                scale=alt.Scale(
                    domain=["monthly_safe_withdraw", "spending"],
                    range=["blue", "red"],
                ),
                legend=alt.Legend(orient="top-left"),
            ),
            tooltip=["key:N"],
        )
    )

    fire_age = summary.fire_age

    vertical_line = (
        alt.Chart(alt.Data(values=[{"fire_age": fire_age}]))
        .mark_rule(strokeDash=[5, 5], color="black")
        .encode(x="fire_age:Q")
    )

    horizontal_line = (
        alt.Chart(alt.Data(values=[{"spending_at_fi": summary.spending_at_fi}]))
        .mark_rule(strokeDash=[5, 5], color="black")
        .encode(y="spending_at_fi:Q")
    )
    chart = alt.layer(base_chart, vertical_line, horizontal_line).properties(
        **_PLOT_PROPERTIES
    )
    return chart.to_json()


def plot_savings_vs_spending(results: list[Results], summary: Summary):
    data = [
        {
            "age": result.age,
            "savings": result.saving,
            "spending": result.spending,
            "investment_profits": result.investment_profits,
        }
        for result in results
    ]

    base_chart = (
        alt.Chart(alt.Data(values=data))
        .transform_fold(
            ["savings", "spending", "investment_profits"], as_=["key", "value"]
        )
        .mark_line()
        .encode(
            x=alt.X("age:Q", title="Age"),
            y=alt.Y("value:Q", title="Monthly Amount"),
            color=alt.Color(
                "key:N",
                title="Legend",
                scale=alt.Scale(
                    domain=["savings", "spending", "investment_profits"],
                    range=["purple", "red", "green"],
                ),
                legend=alt.Legend(orient="top-left"),
            ),
            tooltip=["key:N"],
        )
    )

    fire_age = summary.fire_age

    vertical_line = (
        alt.Chart(alt.Data(values=[{"fire_age": fire_age}]))
        .mark_rule(strokeDash=[5, 5], color="black")
        .encode(x="fire_age:Q")
    )

    saving_horizontal_line = (
        alt.Chart(alt.Data(values=[{"saving_at_fi": summary.saving_at_fi}]))
        .mark_rule(strokeDash=[5, 5], color="purple")
        .encode(y="saving_at_fi:Q")
    )

    spending_horizontal_line = (
        alt.Chart(alt.Data(values=[{"spending_at_fi": summary.spending_at_fi}]))
        .mark_rule(strokeDash=[5, 5], color="red")
        .encode(y="spending_at_fi:Q")
    )

    chart = alt.layer(
        base_chart, vertical_line, saving_horizontal_line, spending_horizontal_line
    ).properties(**_PLOT_PROPERTIES)
    return chart.to_json()


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
):
    dob = datetime.datetime.strptime(date_of_birth, "%Y-%m-%d").date()
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
        "age_vs_net_worth_plot": age_vs_net_worth_plot,
        "age_vs_monthly_safe_withdraw_plot": age_vs_monthly_safe_withdraw_plot,
        "savings_vs_spending_plot": savings_vs_spending_plot,
        "format_currency": format_currency,
        "interpolate_color": interpolate_color,
        "extra_spending": extra_spending,
        "time_difference": time_difference,
        "summary_with_extra": summary_with_extra,
        "url_params": url_params,
    }

    return context


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, log_level="info", reload=True)
