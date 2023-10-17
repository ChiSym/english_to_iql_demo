import polars as pl


def plot_context_first_vars(data_path: str) -> dict:
    df = pl.read_csv(data_path)
    col_names = df.columns
    var1 = col_names[0]
    var2 = col_names[1]

    return plot_context(df, var1, var2)


def get_col_type(df: pl.DataFrame, col: str) -> str:
    if df[col].is_numeric():
        return "quantitative"
    else:
        return "nominal"


def plot_context(df: pl.DataFrame, var1: str, var2: str) -> dict:
    var1_type = get_col_type(df, var1)
    var2_type = get_col_type(df, var2)

    match [var1_type, var2_type]:
        case ["nominal", "nominal"]:
            return {"plot_type": "nn", "var1": var1, "var2": var2}
        case ["quantitative", "quantitative"]:
            return {"plot_type": "qq", "var1": var1, "var2": var2}
        case ["quantitative", "nominal"]:
            return {
                "plot_type": "qn",
                "var1": var1,
                "var2": var2,
                "var1_extent": [df[var1].min(), df[var1].max()],
            }
        case ["nominal", "quantitative"]:
            return {
                "plot_type": "qn",
                "var1": var2,
                "var2": var1,
                "var1_extent": [df[var2].min(), df[var2].max()],
            }
        case _:
            raise NotImplementedError
