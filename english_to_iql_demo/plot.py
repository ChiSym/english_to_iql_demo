import polars as pl
import altair as alt
import json
import logging as log
from collections import Counter
import altair as alt


alt.data_transformers.enable("vegafusion")

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

def plot_dispatch(dsl: str, df: pl.DataFrame) -> dict:
    if dsl == "LPM":
        return plot_lpm(df)
    elif dsl == "data":
        return plot_data(df)
    elif dsl == "OOD":
        return plot_ood(df)
    else:
        raise ValueError

def plot_ood(df: pl.DataFrame) -> dict:
    height = 300
    width = 400
    background="#FFFFFF00" # transparent
    chart = alt.Chart(df).mark_point().encode(
        x='x:Q',
        y='y:Q',
    ).properties(
        height=height,
        width=width,
        background=background
    )
    return {"chart": json.loads(chart.to_json())}

def plot_data(df: pl.DataFrame) -> dict:
    # plot at most 4 variables
    # col_types = [get_col_type(df, col) for col in df.columns[:4]]

    # x_encodings = [
    #     f"{x}:Q" if x_type == "quantitative" else f"{x}:N"
    #     for x, x_type in zip(df.columns[:4], col_types)
    # ]
    x_encodings = df.columns[:4]

    chart = alt.Chart(df, width=300, height=200).mark_bar().encode(
        x=alt.X(alt.repeat('repeat'), type="nominal"),
        y='count()'
    ).repeat(
        repeat=x_encodings,
        columns=2
    )

    return {"chart": json.loads(chart.to_json(format="vega"))}

def plot_lpm(df: pl.DataFrame) -> dict:
    height = 300
    width = 400
    area_opacity = 0.3
    background="#FFFFFF00" # transparent

    # this handles the fact that variable assignment (i.e. X=x)
    # creates columns with a single value
    for col in df.columns:
        if df[col].drop_nulls().n_unique() <= 1:
            df = df.drop(col)

    if len(df) == 0:
        return plot_ood(df)

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
    log.debug(col_counter)
    chart = None
    log.debug(col_counter)
    chart = None

    if col_counter['quantitative'] == 1 and col_counter['nominal'] == 0:
        q_var = nonp_df.columns[0]
        # make sure p is always in the y-axis

        chart = alt.layer(
            alt.Chart(df).mark_line().encode(
                alt.X(f'{q_var}:Q'),
                alt.Y(f'{p_mean_var}:Q', title="probability").scale(zero=False),
                tooltip=[f'{q_var}', f'{p_mean_var}'],
            ).properties(
                height=height,
                width=width,
                background=background
            ),
            alt.Chart(df).mark_area(opacity=area_opacity).encode(
                alt.X(f'{q_var}:Q'),
                alt.Y(f'{p_min_var}:Q'),
                alt.Y2(f'{p_max_var}:Q')
            )
        )

    if col_counter['quantitative'] == 0 and col_counter['nominal'] == 1:
        n_var = nonp_df.columns[0]

        x=alt.X(f'{n_var}:N')

        if n_var in custom_order.keys():
            x = x.sort(custom_order[n_var])

        chart = alt.layer(
            alt.Chart(df).mark_line().encode(
                x=x,
                y=alt.Y(f'{p_mean_var}:Q', title="probability").scale(zero=False),
                tooltip=[f'{n_var}', f'{p_mean_var}'],
            ).properties(
                height=height,
                width=width,
                background=background
            ),
            alt.Chart(df).mark_area(opacity=area_opacity).encode(
                x=x,
                y=alt.Y(f'{p_min_var}:Q'),
                y2=alt.Y2(f'{p_max_var}:Q')
            )
        )

    if col_counter['quantitative'] == 0 and col_counter['nominal'] == 2:
        nominal_idxs = [i for i, x in enumerate(col_types) if x == 'nominal']
        n_var1 = nonp_df.columns[nominal_idxs[0]]
        n_var2 = nonp_df.columns[nominal_idxs[1]]

        if len(df[n_var1].unique()) <= len(df[n_var2].unique()):
            n_var1, n_var2 = n_var2, n_var1

        x=alt.X(f'{n_var1}:N')

        if n_var1 in custom_order.keys():
            x = x.sort(custom_order[n_var1])

        color=alt.Color(f'{n_var2}:N')
        # color=alt.Color(f'{n_var2}:O')

        if n_var2 in custom_order.keys():
            color = color.sort(custom_order[n_var2])
        
        if n_var2 in ordinal_vars:
            color = color.scale(scheme="viridis")

        selection = alt.selection_point(on='click', empty=False)
        cond_opacity = alt.condition(
            selection,
            alt.value(0.3),
            alt.value(0.0)
        )

        chart = alt.layer(
            alt.Chart(df).mark_line().encode(
                x=x,
                y=alt.Y(f'{p_mean_var}:Q', title="probability").scale(zero=False),
                color=color,
                tooltip=[f'{p_mean_var}', f'{n_var1}', f'{n_var2}'],
                order=alt.condition(selection, alt.value(1), alt.value(0))
            )
            .properties(
                height=height,
                width=width
            ),
            alt.Chart(df).mark_area().encode(
                x=x,
                y=alt.Y(f'{p_min_var}:Q'),
                y2=alt.Y2(f'{p_max_var}:Q'),
                color=color,
                opacity=cond_opacity,
                order=alt.condition(selection, alt.value(1), alt.value(0))
            ).add_params(
                selection
            )
        ).properties(
            background=background
        )


    if not chart:
        raise ValueError("No chart type matches the data's column types")
    
    return {"chart": json.loads(chart.to_json(format="vega"))}


def get_col_type(df: pl.DataFrame, col: str) -> str:
    if df[col].dtype == pl.Float32:
        return "quantitative"
    else:
        return "nominal"