from typing import Union

import polars as pl
import json
import pickle
import geopandas as gpd

from jax_multimix.interpreter import Interpreter as ProbInterpreter
from jax_multimix.model import mixture_model, SumProductInference


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
        with open("interpreter_metadata.pkl", "rb") as f:
            prob_interpreter_metadata = pickle.load(f)
            return ProbInterpreter(
                variables=prob_interpreter_metadata["variables"],
                schema=json.load(open("schema.json", "r")),
                model=mixture_model,
                args=prob_interpreter_metadata["args"],
                inf_alg=SumProductInference(),
                df=pl.read_parquet("synthetic_data.parquet", use_pyarrow=True),
                geo_df=geo_df,
            )
    elif grammar_path == "us_lpm_cols.lark":
        with open("us_lpm.json", "r", encoding="utf-8") as f:
            col_interpreter_metadata = json.load(f)[0]
        df = pl.read_parquet("synthetic_data.parquet")
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