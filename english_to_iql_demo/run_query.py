from typing import Union

import polars as pl
import json
import dill

from jax_multimix.interpreter import Interpreter as ProbInterpreter
from jax_multimix.model import mixture_model, SumProductInference, make_variables

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
    data_path = "data.parquet"
    if grammar_path == "us_lpm_prob.lark":
        # override state variable in synthetic data with PUMA state
        df = pl.read_parquet(data_path, use_pyarrow=True)
        schema = json.load(open("schema.json"))
        jaxcat_model = dill.load(open("mixture_model.dill", "rb"))
        
        return ProbInterpreter(
            variables=make_variables(schema),
            schema=schema,
            model=mixture_model,
            args=jaxcat_model,
            inf_alg=SumProductInference(),
            df=df,
        )
    elif grammar_path == "us_lpm_cols.lark":
        with open("us_lpm.json", "r", encoding="utf-8") as f:
            col_interpreter_metadata = json.load(f)[0]
        df = pl.read_parquet(data_path)
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
