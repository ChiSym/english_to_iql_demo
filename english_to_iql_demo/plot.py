import polars as pl
import altair as alt
import json
import logging as log
from collections import Counter
import altair as alt
import geopandas as gpd


alt.data_transformers.enable("vegafusion")

NUMERIC_POLARS_DTYPES = [
    pl.Int8, pl.Int16, pl.Int32, pl.Int64, 
    pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64,
    pl.Float32, pl.Float64, 
]

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
    chart = alt.Chart(df).mark_point(opacity=0).encode(
        x='x:Q',
        y='y:Q',
    ).properties(
        height=height,
        width=width,
        background=background
    )
    return {"chart": json.loads(chart.to_json(format="vega"))}

def plot_data(df: pl.DataFrame) -> dict:
    df = df.drop_nulls()
    # plot at most 4 variables
    col_types = [get_col_type(df, col) for col in df.columns[:4]]

    x_encodings = [
        f"{x}:Q" if x_type == "quantitative" else f"{x}:N"
        for x, x_type in zip(df.columns[:4], col_types)
    ]
    # x_encodings = df.columns[:4]

    charts = [
        alt.Chart(df, width=300, height=200).mark_bar().encode(
            x=alt.X(f"{x}:Q", bin=True),
            y='count()'
    )
        if x_type == "quantitative" else alt.Chart(df, width=300, height=200).mark_bar().encode(
            x=alt.X(f"{x}:N"),
            y='count()'
        )
        for x, x_type in zip(df.columns[:4], col_types)
    ]

    # a bit clunky but it'll do for now---the issue is that 
    # I couldn't get `repeat` to work with the varying Q and N plots
    if len(charts) == 1:
        chart = charts[0]
    if len(charts) == 2:
        chart = charts[0] | charts[1]
    if len(charts) == 3:
        chart = (charts[0] | charts[1]) & charts[2]
    elif len(charts) == 4:
        chart = (charts[0] | charts[1]) & (charts[2] | charts[3])

    return {"chart": json.loads(chart.to_json(format="vega"))}

def plot_lpm(df: pl.DataFrame) -> dict:
    height = 300
    width = 400
    background="#FFFFFF00" # transparent

    if isinstance(df, gpd.GeoDataFrame):
        df = df[['geometry', 'probability']]
        chart = alt.Chart(df).mark_geoshape().encode(
            alt.Color("probability:Q")
        ).project(
            type='albersUsa'
        ).properties(
                height=height,
                width=width,
            )
        return {"chart": json.loads(chart.to_json(format="vega"))}

    df = df.drop_nulls()
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
    p_df = df.select(
        pl.col('^p_.*$'),
        pl.col("model"),
        pl.col('^weight_.*$')
        )
    nonp_df = df.select(
        pl.exclude(
            '^p_.*$',
            "model",
            '^weight_.*$'
        ))
    assert len(p_df.columns) == 4
    # TODO make this nicer
    p_mean_var = p_df.select(pl.col('^p_mean.*$')).columns[0]
    p_sample_var = p_df.select(pl.col('^p_sample.*$')).columns[0]
    weight_var = p_df.select(pl.col('^weight.*$')).columns[0]

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
            ),
            alt.Chart(df).mark_circle().encode(
                alt.X(f'{q_var}:Q'),
                alt.Y(f'{p_sample_var}:Q'),
                alt.Opacity(f'{weight_var}:Q', legend=None)
            )
        ).properties(
            background=background
        )

    if col_counter['quantitative'] == 0 and col_counter['nominal'] == 1:
        n_var = nonp_df.columns[0]

        x=alt.X(f'{n_var}:N')

        if n_var in custom_order.keys():
            x = x.sort(custom_order[n_var])

        chart = alt.layer(
            alt.Chart(df).mark_bar(filled=False).encode(
                x=x,
                y=alt.Y(f'mean({p_mean_var}):Q', title="probability").scale(zero=False),
                tooltip=[f'{n_var}', f'{p_mean_var}'],
            ).properties(
                height=height,
                width=width,
            ),
            alt.Chart(df).mark_circle().encode(
                x=x,
                y=alt.Y(f'{p_sample_var}:Q'),
                opacity=alt.Opacity(f'{weight_var}:Q', legend=None)
            )
        ).properties(
            background=background
        )

    if col_counter['quantitative'] == 1 and col_counter['nominal'] == 1:
        nominal_idx = [i for i, x in enumerate(col_types) if x == 'nominal'][0]
        continuous_idx = [i for i, x in enumerate(col_types) if x == 'quantitative'][0]
        n_var = nonp_df.columns[nominal_idx]
        q_var = nonp_df.columns[continuous_idx]

        x=alt.X(f'{q_var}:Q')

        color=alt.Color(f'{n_var}:N')
        # color=alt.Color(f'{n_var2}:O')

        if n_var in custom_order.keys():
            color = color.sort(custom_order[n_var])
        
        if n_var in ordinal_vars:
            color = color.scale(scheme="viridis")

        group_col = n_var

        selection = alt.selection_point(
            on='click', 
            # what should the selection return when nothing is selected? altair weirdly selects *everything*
            empty=False, 
            # necessary to make clicking nearby work, else hitting a line is really hard, surprisingly
            nearest=True, 
            # extends selection to everything with the same val in the group_col, and not just the actual value clicked on
            fields=[group_col] 
        )

        # opacity is based on weight var when selected, invisible otherwise
        cond_opacity = alt.condition(
            selection,
            alt.Opacity(f'{weight_var}:Q', legend=None),
            alt.value(0.0)
        )

        # Needed for visible line, and invisible point marks
        shared_line_encoding = {
            "x": x,
            "y": alt.Y(f'{p_mean_var}:Q', title="probability").scale(zero=False)
        }

        chart = alt.layer(
            alt.Chart(df).mark_line().encode(
                color=color,
                strokeWidth=alt.condition(selection, alt.value(5), alt.value(2)),
                **shared_line_encoding
            ),
            # These invisible point marks exist to support "nearest" selection, 
            # which doesn't work well with line/area marks
            alt.Chart(df).mark_point().encode(
                opacity = {"value": 0},
                **shared_line_encoding
            ).add_params( # adding this to other views breaks clicking, just add to the one used for targeting
                selection
            ),
            alt.Chart(df).mark_circle().encode(
                x=x,
                y=alt.Y(f'{p_sample_var}:Q'),
                color=color,
                opacity=cond_opacity,
            )
        ).properties(
            height=height,
            width=width
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

        group_col = n_var2

        selection = alt.selection_point(
            on='click', 
            # what should the selection return when nothing is selected? altair weirdly selects *everything*
            empty=False, 
            # necessary to make clicking nearby work, else hitting a line is really hard, surprisingly
            nearest=True, 
            # extends selection to everything with the same val in the group_col, and not just the actual value clicked on
            fields=[group_col] 
        )

        # opacity is based on weight var when selected, invisible otherwise
        cond_opacity = alt.condition(
            selection,
            alt.Opacity(f'{weight_var}:Q', legend=None),
            alt.value(0.0)
        )

        # Needed for visible line, and invisible point marks
        shared_line_encoding = {
            "x": x,
            "y": alt.Y(f'mean({p_mean_var}):Q', title="probability").scale(zero=False)
        }
        
        chart = alt.layer(
            alt.Chart(df).mark_bar(filled=False).encode(
                color=color,
                xOffset=color,
                strokeWidth=alt.condition(selection, alt.value(5), alt.value(2)),
                **shared_line_encoding
            ),
            # These invisible point marks exist to support "nearest" selection, 
            # which doesn't work well with line/area marks
            alt.Chart(df).mark_point().encode(
                opacity = {"value": 0},
                xOffset=color,
                **shared_line_encoding
            ).add_params( # adding this to other views breaks clicking, just add to the one used for targeting
                selection
            ),
            alt.Chart(df).mark_circle().encode(
                x=x,
                y=alt.Y(f'{p_sample_var}:Q'),
                xOffset=color,
                color=color,
                opacity=cond_opacity,
            )
        ).properties(
            height=height,
            width=width
        )

    if col_counter['quantitative'] == 2 and col_counter['nominal'] == 0:
        quantitative_idxs = [i for i, x in enumerate(col_types) if x == 'quantitative']
        q_var1 = nonp_df.columns[quantitative_idxs[0]]
        q_var2 = nonp_df.columns[quantitative_idxs[1]]

        x=alt.X(f'{q_var1}:Q')
        color=alt.Color(f'{q_var2}:Q')
        color = color.scale(scheme="viridis")

        group_col = q_var2

        selection = alt.selection_point(
            on='click', 
            # what should the selection return when nothing is selected? altair weirdly selects *everything*
            empty=False, 
            # necessary to make clicking nearby work, else hitting a line is really hard, surprisingly
            nearest=True, 
            # extends selection to everything with the same val in the group_col, and not just the actual value clicked on
            fields=[group_col] 
        )

        # opacity is based on weight var when selected, invisible otherwise
        cond_opacity = alt.condition(
            selection,
            alt.Opacity(f'{weight_var}:Q', legend=None),
            alt.value(0.0)
        )

        # Needed for visible line, and invisible point marks
        shared_line_encoding = {
            "x": x,
            "y": alt.Y(f'{p_mean_var}:Q', title="probability").scale(zero=False)
        }

        chart = alt.layer(
            alt.Chart(df).mark_line().encode(
                color=color,
                strokeWidth=alt.condition(selection, alt.value(5), alt.value(2)),
                **shared_line_encoding
            ),
            # These invisible point marks exist to support "nearest" selection, 
            # which doesn't work well with line/area marks
            alt.Chart(df).mark_point().encode(
                opacity = {"value": 0},
                **shared_line_encoding
            ).add_params( # adding this to other views breaks clicking, just add to the one used for targeting
                selection
            ),
            alt.Chart(df).mark_circle().encode(
                x=x,
                y=alt.Y(f'{p_sample_var}:Q'),
                color=color,
                opacity=cond_opacity,
            )
        ).properties(
            height=height,
            width=width
        )

    if not chart:
        raise ValueError("No chart type matches the data's column types")
    
    return {"chart": json.loads(chart.to_json(format="vega"))}


def get_col_type(df: pl.DataFrame, col: str) -> str:
    if df[col].dtype in NUMERIC_POLARS_DTYPES:
        return "quantitative"
    else:
        return "nominal"