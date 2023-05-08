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
    safe_withdraw_withdrawal_rate: float = 4

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
    months: int
    nw: float
    income: float
    spending: float
    delta_nw: float
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
        return self.income - self.spending

    @property
    def safe_withdraw_rule_yearly(self) -> float:
        return self.nw * self.input_data.safe_withdraw_withdrawal_rate / 100

    @property
    def safe_withdraw_minus_spending(self) -> float:
        return self.safe_withdraw_rule_monthly - self.spending

    @property
    def investment_profits(self) -> float:
        return self.nw * self.input_data.monthly_growth_rate - self.nw

    def next_month(self) -> "Results":
        new_nw = self.nw + self.investment_profits + self.saving
        new_months = self.months + 1
        new_spending = self.spending * self.input_data.monthly_inflation
        new_income = self.income * self.input_data.monthly_salary_increase_rate
        new_delta_nw = new_nw - self.nw
        return Results(
            months=new_months,
            nw=new_nw,
            delta_nw=new_delta_nw,
            income=new_income,
            spending=new_spending,
            input_data=self.input_data,
        )


class Summary(BaseModel):
    age: float
    fire_age: float
    fire_date: date
    years_till_fi: float
    saving_at_fi: float
    safe_withdraw_at_fi: float
    spending_at_fi: float
    nw_at_fi: float
    safe_withdraw_at_35: Optional[float]
    safe_withdraw_at_40: Optional[float]
    safe_withdraw_at_45: Optional[float]

    @classmethod
    def from_results(cls, results: list[Results]) -> Summary | None:
        r = next((r for r in results if r.safe_withdraw_minus_spending > 0), None)
        if r is None:
            return None
        return cls(
            age=r.input_data.age,
            fire_date=r.date,
            fire_age=r.age,
            years_till_fi=r.years,
            safe_withdraw_at_fi=r.safe_withdraw_rule_monthly,
            spending_at_fi=r.spending,
            saving_at_fi=r.saving,
            nw_at_fi=r.nw,
            safe_withdraw_at_35=next(
                (r.safe_withdraw_rule_yearly for r in results if int(r.age) == 35), None
            ),
            safe_withdraw_at_40=next(
                (r.safe_withdraw_rule_yearly for r in results if int(r.age) == 40), None
            ),
            safe_withdraw_at_45=next(
                (r.safe_withdraw_rule_yearly for r in results if int(r.age) == 45), None
            ),
        )


app = FastAPI()
app.mount("/static", StaticFiles(directory=FOLDER / "static"), name="static")
templates = Jinja2Templates(directory=FOLDER / "templates")


@app.get("/", response_class=HTMLResponse)
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
):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "growth_rate": growth_rate,
            "current_nw": current_nw,
            "spending_per_month": spending_per_month,
            "inflation": inflation,
            "annual_salary_increase": annual_salary_increase,
            "income_per_month": income_per_month,
            "extra_income": extra_income,
            "date_of_birth": date_of_birth,
        },
    )


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
        saving=data.saving_per_month,
        income=data.income_per_month,
        spending=data.spending_per_month,
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
    data = [{"age": result.age, "net_worth": result.nw} for result in results]

    base_chart = (
        alt.Chart(alt.Data(values=data))
        .mark_line()
        .encode(
            x=alt.X("age:Q", title="Age"),
            y=alt.Y("net_worth:Q", title="Net Worth"),
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

    return alt.layer(base_chart, vertical_line, horizontal_line).to_json()


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
                    domain=["monthly_safe_withdraw", "spending"], range=["blue", "red"]
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

    return alt.layer(base_chart, vertical_line, horizontal_line).to_json()


def plot_savings_vs_spending(results: list[Results], summary: Summary):
    data = [
        {"age": result.age, "savings": result.saving, "spending": result.spending}
        for result in results
    ]

    base_chart = (
        alt.Chart(alt.Data(values=data))
        .transform_fold(["savings", "spending"], as_=["key", "value"])
        .mark_line()
        .encode(
            x=alt.X("age:Q", title="Age"),
            y=alt.Y("value:Q", title="Amount"),
            color=alt.Color(
                "key:N",
                title="Legend",
                scale=alt.Scale(
                    domain=["savings", "spending"], range=["purple", "red"]
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

    return alt.layer(
        base_chart, vertical_line, saving_horizontal_line, spending_horizontal_line
    ).to_json()


def format_currency(value):
    return "${:,.0f}".format(value).replace(",", ".")


@app.get("/calculate", response_class=HTMLResponse)
def calculate(
    request: Request,
    growth_rate: float = Query(...),
    current_nw: float = Query(...),
    spending_per_month: float = Query(...),
    inflation: float = Query(...),
    annual_salary_increase: float = Query(...),
    income_per_month: float = Query(...),
    extra_income: float = Query(...),
    date_of_birth: str = Query(...),
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
    )
    results = calculate_results_for_month(input_data)
    summary = Summary.from_results(results)
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

    return templates.TemplateResponse(
        "index.html",
        {
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
            "age_vs_net_worth_plot": age_vs_net_worth_plot,
            "age_vs_monthly_safe_withdraw_plot": age_vs_monthly_safe_withdraw_plot,
            "savings_vs_spending_plot": savings_vs_spending_plot,
            "format_currency": format_currency,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, log_level="info", reload=True)
