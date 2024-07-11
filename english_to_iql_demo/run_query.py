# import polars as pl

# # def run_query(parser, interpreter, query):
# def run_query(parser, query):
#     tree = parser.parse(query)
#     # df = interpreter.transform(tree)

#     df = pl.DataFrame({
#         'A': [1, 2, 3, 4, 5],
#         'B': ['a', 'b', 'c', 'd', 'e'],
#         'p_mean': [0.1, 0.2, 0.3, 0.4, 0.5],
#         'p_max': [0.19, 0.25, 0.39, 0.42, 0.58],
#         'p_min': [0.01, 0.12, 0.13, 0.34, 0.45]
#         },
#         schema=[("A", pl.Float32),
#                 ("B", pl.Categorical), 
#                 ("p_mean", pl.Float32), 
#                 ("p_max", pl.Float32), 
#                 ("p_min", pl.Float32)])

#     # currently getting some nulls, will investigate 
#     return df.drop_nulls()

import polars as pl

def run_query(parser, query):
    tree = parser.parse(query)
    # df = interpreter.transform(tree)

    df = pl.DataFrame({
        'A': ["foo", "bar", "baz", "quux", "moop", "baz", "bar", "quux", "moop", "foo"],
        'B': ['a', 'a', 'a', 'a', 'a', 'b', 'b', 'b', 'b', 'b'],
        'p_mean': [0.1, 0.2, 0.3, 0.4, 0.5, 0.08, 0.21, 0.31, 0.41, 0.495],
        'p_max': [0.19, 0.25, 0.39, 0.42, 0.58, 0.19, 0.25, 0.39, 0.42, 0.58],
        'p_min': [0.01, 0.12, 0.13, 0.34, 0.45, 0.01, 0.12, 0.13, 0.34, 0.45]
    },
    schema=[
        ("X", pl.Categorical),
        ("B", pl.Categorical),
        ("p_mean", pl.Float32),
        ("p_max", pl.Float32),
        ("p_min", pl.Float32)
    ])

    # currently getting some nulls, will investigate 
    return df.drop_nulls()
