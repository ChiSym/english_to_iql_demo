from typing import Union

import json
import pickle

from jax_multimix.interpreter import Interpreter as ProbInterpreter
from jax_multimix.model import mixture_model, SumProductInference


class ColumnInterpreter:
    def __init__(self, datadict):
        self.datadict = datadict

    def transform(self, tree):
        keep = []
        for st in tree.iter_subtrees():
            if st.data.value=="var":
                keep.append(st.children[0].value)
        return {k: self.datadict[k] for k in keep}

Interpreter = Union[ProbInterpreter, ColumnInterpreter]


def interpreter_dispatch(grammar_path):
    if grammar_path == "us_lpm_prob.lark":
        with open("interpreter_metadata.pkl", "rb") as f:
            prob_interpreter_metadata = pickle.load(f)
            return ProbInterpreter(
            variables=prob_interpreter_metadata["variables"],
            schema=prob_interpreter_metadata["schema"],
            model=mixture_model,
            args=prob_interpreter_metadata["args"],
            inf_alg=SumProductInference(),
        )
    elif grammar_path == "us_lpm_cols.lark":
        with open("us_lpm.json", "r", encoding="utf-8") as f:
            col_interpreter_metadata = json.load(f)[0]
        return ColumnInterpreter(col_interpreter_metadata)
    else:
        raise NotImplementedError(f"Preprompt constructor not yet defined for {grammar_path}.")


def run_query(parser, interpreter, query):
    bos, eos = " ", "\n"
    query = bos + query + eos
    tree = parser.parse(query)
    out = interpreter.transform(tree)
    if isinstance(interpreter, ProbInterpreter):
        # currently getting some nulls, will investigate
        return out.drop_nulls()
    return out
