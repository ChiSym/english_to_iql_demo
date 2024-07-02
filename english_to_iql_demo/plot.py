import polars as pl
import altair as alt
import json
from collections import Counter

custom_order  = {"Credit_rating": [
        "Under 499",
        "500-549",
        "550-599",
        "600-649",
        "650-699",
        "700-749",
        "750-799",
        "800+"],
}
ordinal_vars = ["Credit_rating", "Total_income", "Commute_minutes", "Education"]


def plot(df: pl.DataFrame) -> dict:
    width = 600
    height = 400

    if len(df) >= 5000:
        df = df.sample(n=4999, seed=0) 

    if len(df) == 0:
        chart = alt.Chart(df).mark_point().encode(
            x='x:Q',
            y='y:Q',
            ).properties(
            width=width,
            height=height
        )
        return {"chart": json.loads(chart.to_json())}

    # for now, plot at most 3 variables
    col_types = [get_col_type(df, col) for col in df.columns[:3]]

    col_counter = Counter(col_types)

    if col_counter['quantitative'] == 2 and col_counter['nominal'] == 0:
        quantitative_idxs = [i for i, x in enumerate(col_types) if x == 'quantitative']
        q_var1 = df.columns[quantitative_idxs[0]]
        q_var2 = df.columns[quantitative_idxs[1]]

        # make sure p is always in the y-axis
        if q_var1 == "p":
            q_var1, q_var2 = q_var2, q_var1

        chart = alt.Chart(df).mark_line().encode(
            x=alt.X(f'{q_var1}:Q'),
            y=alt.Y(f'{q_var2}:Q').scale(zero=False),
            tooltip=[f'{q_var1}', f'{q_var2}'],
        ).properties(
            width=width,
            height=height
        )

    if col_counter['quantitative'] == 1 and col_counter['nominal'] == 1:
        n_var = df.columns[col_types.index('nominal')]
        q_var = df.columns[col_types.index('quantitative')]

        x=alt.X(f'{n_var}:N')

        if n_var in custom_order.keys():
            x = x.sort(custom_order[n_var])

        chart = alt.Chart(df).mark_line().encode(
            x=x,
            y=alt.Y(f'{q_var}:Q').scale(zero=False),
            tooltip=[f'{n_var}', f'{q_var}'],
        ).properties(
            width=width,
            height=height
        )

    if col_counter['quantitative'] == 1 and col_counter['nominal'] == 2:
        nominal_idxs = [i for i, x in enumerate(col_types) if x == 'nominal']
        n_var1 = df.columns[nominal_idxs[0]]
        n_var2 = df.columns[nominal_idxs[1]]
        q_var = df.columns[col_types.index('quantitative')]

        x=alt.X(f'{n_var1}:N')

        if n_var1 in custom_order.keys():
            x = x.sort(custom_order[n_var1])

        color=alt.Color(f'{n_var2}:N')

        if n_var2 in custom_order.keys():
            color = color.sort(custom_order[n_var2])
        
        if n_var2 in ordinal_vars:
            color = color.scale(scheme="viridis")

        chart = alt.Chart(df).mark_line().encode(
            x=x,
            y=alt.Y(f'{q_var}:Q').scale(zero=False),
            color=color,
            tooltip=[f'{q_var}', f'{n_var1}', f'{n_var2}'],
        ).properties(
            width=width,
            height=height
        )

    return {"chart": json.loads(chart.to_json())}


def get_col_type(df: pl.DataFrame, col: str) -> str:
    if df[col].is_numeric():
        return "quantitative"
    else:
        return "nominal"