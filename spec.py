import pickle
from dataclasses import dataclass
from typing import Dict, List

from lark import Lark
import polars as pl

from jax_multimix.interpreter import Interpreter
from jax_multimix.model import mixture_model, SumProductInference

from english_to_iql_demo.english_to_iql import english_query_to_iql_posterior
from english_to_iql_demo.run_query import run_query


@dataclass
class Data:
    english_query: str
    grammar_paths: List[str]
    grammars: List[str]
    parsers: List[Lark]
    genparse_urls: List[str]
    posteriors: List[Dict[str, float]]
    log_ml_estimates: List[float]
    queries: List[str]
    interpreter: Interpreter
    df: pl.DataFrame



def main():

    def load_grammar(grammar_path):
        with open(f"grammars/{grammar_path}", "r", encoding="utf-8") as f:
            grammar_str = f.read()
        return grammar_str

    # TODO: fill in "us_lpm_cols.lark" with correct grammar
    grammar_paths = ["us_lpm_prob.lark", "us_lpm_cols.lark"]
    grammars = list(map(load_grammar, grammar_paths))
    parsers = list(map(Lark, grammars))
    indices = range(len(grammar_paths))

    # temp approach
    # as we scale, should set up a load balancer that dispatches to multiple endpoints
    # in interim can just dispatch to two endpoints
    # TODO: update to 2 endpoints
    genparse_backends = ["http://34.122.30.137:8888/infer" for _ in indices]

    # TODO: either extend the interpreter to handle expressions from the column DSL
    # or create a new interpreter for the column DSL
    interpreter_metadata = pickle.load(open("interpreter_metadata.pkl", "rb"))
    interpreter = Interpreter(
        variables=interpreter_metadata["variables"],
        schema=interpreter_metadata["schema"],
        model=mixture_model,
        args=interpreter_metadata["args"],
        inf_alg=SumProductInference(),
    )

    data = Data(
        english_query="",
        grammar_paths=grammar_paths,
        grammars=grammars,
        parsers=parsers,
        genparse_urls=genparse_backends,
        posteriors=[{"": 1.0} for _ in indices],
        log_ml_estimates=[-float("inf") for _ in indices],
        queries=["" for _ in indices],
        interpreter=interpreter,
        df=pl.DataFrame(),
    )

    def run_query_using_best_dsl(data):
        def score_query_dsls(data):
            def score_query_dsl(data, idx):
                data.posteriors[idx], data.log_ml_estimates[idx] = english_query_to_iql_posterior(
                    data.english_query, data.genparse_urls[idx], data.grammars[idx], data.grammar_paths[idx]
                )
                map_particle = max(data.posteriors[idx], key=data.posteriors[idx].get).split('\n')[0].strip() + "\n"
                data.queries[idx] = map_particle

            # TODO: parallelize this
            [score_query_dsl(data, idx) for idx in indices]
            return None

        def select_best_dsl(data):
            return max(indices, key=lambda idx: data.log_ml_estimates[idx])

        score_query_dsls(data)
        idx = select_best_dsl(data)
        df = run_query(data.parsers[idx], data.interpreter, data.queries[idx])
        return df

    data.english_query = "what is the relationship between commute time and age?"
    df = run_query_using_best_dsl(data)
    print(df)

    english_cols_query = "tell me what are variables related to education in this model?"
    # TODO: test once we have the correct grammar


if __name__ == "__main__":
    main()
