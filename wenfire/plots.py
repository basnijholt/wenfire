import altair as alt


from .fire import Results, Summary

_PLOT_PROPERTIES = dict(width=360, usermeta={"embedOptions": {"actions": False}})


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
            "income": result.income,
        }
        for result in results
    ]

    base_chart = (
        alt.Chart(alt.Data(values=data))
        .transform_fold(
            ["monthly_safe_withdraw", "spending", "income"], as_=["key", "value"]
        )
        .mark_line()
        .encode(
            x=alt.X("age:Q", title="Age"),
            y=alt.Y("value:Q", title="Montly Amount"),
            color=alt.Color(
                "key:N",
                title="Legend",
                scale=alt.Scale(
                    domain=["monthly_safe_withdraw", "spending", "income"],
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
