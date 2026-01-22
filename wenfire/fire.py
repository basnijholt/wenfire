from __future__ import annotations

import datetime
import uuid

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, Field


def _today() -> datetime.date:
    return datetime.date.today()


class ParameterChange(BaseModel):
    date: datetime.date
    field: str
    value: float
    uuid: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])


class InputData(BaseModel):
    growth_rate: float
    spending_per_month: float
    inflation: float
    annual_salary_increase: float
    income_per_month: float
    extra_income: float
    # Above can also be in ParameterUpdate
    current_nw: float
    date_of_birth: datetime.date
    safe_withdraw_rate: float = 4
    post_fire_spending_per_month: float | None = (
        None  # Post-FIRE spending (e.g., for moving to cheaper country)
    )
    parameter_changes: list[ParameterChange] = []

    @property
    def now(self):
        return _today()

    def age_at(self, date: datetime.date) -> float:
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
    post_fire_spending: float | None = (
        None  # Post-FIRE target spending (inflation-adjusted)
    )
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
    def fire_spending_target(self) -> float:
        """The spending used for FIRE calculation (post-FIRE if set, else current)."""
        return (
            self.post_fire_spending
            if self.post_fire_spending is not None
            else self.spending
        )

    @property
    def safe_withdraw_minus_spending(self) -> float:
        """Difference between safe withdrawal and FIRE spending target."""
        return self.safe_withdraw_rule_monthly - self.fire_spending_target

    @property
    def investment_profits(self) -> float:
        return self.nw * self.input_data.monthly_growth_rate - self.nw

    @property
    def total_investment_profits(self) -> float:
        return self.nw - self.total_saved

    def next_month(self) -> "Results":
        while (
            self.input_data.parameter_changes
            and self.input_data.parameter_changes[0].date
            and self.date >= self.input_data.parameter_changes[0].date
        ):
            change = self.input_data.parameter_changes.pop(0)
            print(f"Changing {change.field} to {change.value} at {change.date}")
            if change.field in ("growth_rate", "inflation", "annual_salary_increase"):
                setattr(self.input_data, change.field, change.value)
            elif change.field == "income_per_month":
                self.income = change.value
            elif change.field == "extra_income":
                self.extra_income = change.value
            elif change.field == "spending_per_month":
                self.spending = change.value
            else:
                raise ValueError(f"Unknown field {change.field}")

        new_nw = self.nw + self.investment_profits + self.saving
        new_months = self.months + 1
        new_spending = self.spending * self.input_data.monthly_inflation
        new_post_fire_spending = (
            self.post_fire_spending * self.input_data.monthly_inflation
            if self.post_fire_spending is not None
            else None
        )
        new_income = self.income * self.input_data.monthly_salary_increase_rate
        new_delta_nw = new_nw - self.nw
        new_saved = self.total_saved + self.saving
        return Results(
            months=new_months,
            nw=new_nw,
            income=new_income,
            extra_income=self.extra_income,
            spending=new_spending,
            post_fire_spending=new_post_fire_spending,
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
    fire_date: datetime.date
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

        post_fire_spending: float | None = None
        if (
            second_last.post_fire_spending is not None
            and last.post_fire_spending is not None
        ):
            post_fire_spending = interpolate(
                second_last.post_fire_spending, last.post_fire_spending, fraction
            )
        return Results(
            months=interpolated_months,
            nw=interpolate(second_last.nw, last.nw, fraction),
            income=interpolate(second_last.income, last.income, fraction),
            extra_income=second_last.extra_income,
            spending=interpolate(second_last.spending, last.spending, fraction),
            post_fire_spending=post_fire_spending,
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


def calculate_results_for_month(
    data: InputData,
    target: int | datetime.date | None = None,
) -> list[Results]:
    # If target is a date, calculate the target month
    if isinstance(target, datetime.date):
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
        post_fire_spending=data.post_fire_spending_per_month,
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
            if done_for >= 6 * 12:  # 6 years
                break
    return results
