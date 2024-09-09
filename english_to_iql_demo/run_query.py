from typing import Union

import polars as pl
import json
import pickle
import geopandas as gpd

from jax_multimix.interpreter import Interpreter as ProbInterpreter
from jax_multimix.model import mixture_model, SumProductInference, make_GenJax_mixture, make_variables

class ColumnInterpreter:
    def __init__(self, datadict, df):
        self.datadict = datadict
        self.df = df

    def transform(self, tree):
        keep = []
        for st in tree.iter_subtrees():
            if st.data.value=="var":
                keep.append(st.children[0].value)

        # return {k: self.datadict[k] for k in keep}
        return self.df[keep]

Interpreter = Union[ProbInterpreter, ColumnInterpreter]

def interpreter_dispatch(grammar_path):
    if grammar_path == "us_lpm_prob.lark":
        geo_df=gpd.read_file('geodataframe.gpkg', engine='pyogrio', use_arrow=True)
        s = geo_df["geometry"].simplify(1e-2)
        geo_df["geometry"] = s
        df = pl.read_parquet("synthetic_data800k.parquet", use_pyarrow=True)
        # override state variable in synthetic data with PUMA state
        df = df.with_columns(
            pl.col("State_PUMA10")
            .str.split_exact("--", 0)
            .struct.rename_fields(["State_new"])
            .alias("fields")
        ).unnest("fields").select(pl.exclude('State')).rename(
            {"State_new": "State"}
        )
        with open("schema.json", "r") as f:
            schema=json.load(f)
        with open("lpm_parameters.json", "r") as f:
            parameters=json.load(f)
        return ProbInterpreter(
            variables=make_variables(schema),
            schema=schema,
            model=mixture_model,
            args=make_GenJax_mixture(parameters),
            inf_alg=SumProductInference(),
            df=df,
            geo_df=geo_df,
        )
    elif grammar_path == "us_lpm_cols.lark":
        with open("us_lpm.json", "r", encoding="utf-8") as f:
            col_interpreter_metadata = json.load(f)[0]
        df = pl.read_parquet("synthetic_data800k.parquet")
        return ColumnInterpreter(col_interpreter_metadata, df)
    else:
        raise NotImplementedError(f"Preprompt constructor not yet defined for {grammar_path}.")

def run_query(parser, interpreter, query):
    bos, eos = " ", "\n"
    # restrip to handle user-inserted spaces
    query = bos + query.strip() + eos
    tree = parser.parse(query)
    out = interpreter.transform(tree)
    if isinstance(interpreter, ProbInterpreter):
        # currently getting some nulls, will investigate
        return out
    return out
