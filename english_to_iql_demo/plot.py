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

    # this gets around altair's protests against plotting >5000 points
    # TODO: look into vegafusion as a better solution
    if len(df) >= 5000:
        df = df.sample(n=4999, seed=0) 

    # this handles the fact that variable assignment (i.e. X=x)
    # creates columns with a single value
    for col in df.columns:
        if df[col].drop_nulls().n_unique() <= 1:
            df = df.drop(col)

    if len(df) == 0:
        chart = alt.Chart(df).mark_point().encode(
            x='x:Q',
            y='y:Q',
            ).properties(
            width=width,
            height=height
        )
        return {"chart": json.loads(chart.to_json())}

    # for now, we're going to assume that we're only getting results
    # for probability_of queries
    # and we're always going to plot p_ on the y-axis
    # that means we'll have continuous variables p_..., p_min_..., p_max_...
    # + whichever continuous and discrete variables we have mentioned in the query
    p_df = df.select(pl.col('^p_.*$'))
    nonp_df = df.select(pl.exclude('^p_.*$'))
    assert len(p_df.columns) == 3
    # TODO make this nicer
    p_mean_var = p_df.select(pl.col('^p_mean.*$')).columns[0]
    p_min_var = p_df.select(pl.col('^p_min.*$')).columns[0]
    p_max_var = p_df.select(pl.col('^p_max.*$')).columns[0]

    # for now, plot at most 3 variables
    col_types = [get_col_type(nonp_df, col) for col in nonp_df.columns[:3]]

    col_counter = Counter(col_types)

    if col_counter['quantitative'] == 1 and col_counter['nominal'] == 0:
        q_var = nonp_df.columns[0]
        # make sure p is always in the y-axis

        chart = alt.Chart(df).mark_line().encode(
            x=alt.X(f'{q_var}:Q'),
            y=alt.Y(f'{p_mean_var}:Q').scale(zero=False),
            tooltip=[f'{q_var}', f'{p_mean_var}'],
        ).properties(
            width=width,
            height=height
        )

    if col_counter['quantitative'] == 0 and col_counter['nominal'] == 1:
        n_var = nonp_df.columns[0]

        x=alt.X(f'{n_var}:N')

        if n_var in custom_order.keys():
            x = x.sort(custom_order[n_var])

        chart = alt.Chart(df).mark_line().encode(
            x=x,
            y=alt.Y(f'{p_mean_var}:Q').scale(zero=False),
            tooltip=[f'{n_var}', f'{p_mean_var}'],
        ).properties(
            width=width,
            height=height
        )

    if col_counter['quantitative'] == 0 and col_counter['nominal'] == 2:
        nominal_idxs = [i for i, x in enumerate(col_types) if x == 'nominal']
        n_var1 = nonp_df.columns[nominal_idxs[0]]
        n_var2 = nonp_df.columns[nominal_idxs[1]]

        x=alt.X(f'{n_var1}:N')

        if n_var1 in custom_order.keys():
            x = x.sort(custom_order[n_var1])

        color=alt.Color(f'{n_var2}:N')
        # color=alt.Color(f'{n_var2}:O')

        if n_var2 in custom_order.keys():
            color = color.sort(custom_order[n_var2])
        
        if n_var2 in ordinal_vars:
            color = color.scale(scheme="viridis")

        chart = alt.Chart(df).mark_line().encode(
            x=x,
            y=alt.Y(f'{p_mean_var}:Q').scale(zero=False),
            color=color,
            tooltip=[f'{p_mean_var}', f'{n_var1}', f'{n_var2}'],
        ).properties(
            width=width,
            height=height
        )

    return {"chart": json.loads(chart.to_json())}


def get_col_type(df: pl.DataFrame, col: str) -> str:
    if df[col].dtype == pl.Float32:
        return "quantitative"
    else:
        return "nominal"