import pickle
from dataclasses import dataclass

from lark import Lark
import polars as pl

from jax_multimix.interpreter import Interpreter
from jax_multimix.model import mixture_model, SumProductInference

from english_to_iql_demo.english_to_iql import english_query_to_iql_posterior
from english_to_iql_demo.run_query import run_query


@dataclass
class Data:
    grammar_path: str
    grammar: str
    parser: Lark
    english_query: str
    genparse_url: str
    posterior: dict
    log_ml_estimate: float
    query: str
    interpreter: Interpreter
    df: pl.DataFrame


def build_parser(lark_grammar_path):
    with open(f"grammars/{lark_grammar_path}", "r", encoding="utf-8") as f:
        lark_grammar_str = f.read()
    parser = Lark(lark_grammar_str)
    return parser


def main():

    # TODO: fill in "us_lpm_cols.lark" with correct grammar
    grammar_paths = ["us_lpm_prob.lark", "us_lpm_cols.lark"]
    parsers = [build_parser(gp) for gp in grammar_paths]

    # temp approach
    # as we scale, should set up a load balancer that dispatches to multiple endpoints
    # in interim can just dispatch to two endpoints
    # TODO: update to 2 endpoints
    genparse_backends = ["http://34.122.30.137:8888/infer" for _ in range(len(parsers))]

    interpreter_metadata = pickle.load(open("interpreter_metadata.pkl", "rb"))
    interpreter = Interpreter(
        variables=interpreter_metadata["variables"],
        schema=interpreter_metadata["schema"],
        model=mixture_model,
        args=interpreter_metadata["args"],
        inf_alg=SumProductInference(),
    )

    data_structs = [
        Data(
            grammar_path=gp,
            grammar=parser.source_grammar,
            parser=parser,
            english_query="",
            genparse_url=backend,
            posterior={},
            log_ml_estimate=-float("inf"),
            query="",
            interpreter=interpreter,
            df=pl.DataFrame(),
        )
        for gp, parser, backend in zip(grammar_paths, parsers, genparse_backends)
    ]

    def score_query_dsls(english_query):
        # TODO: parallelize this
        for data in data_structs:
            data.english_query = english_query
            # TODO: implement `make_cols_pre_prompt` to prep prompts for col queries
            data.posterior, data.log_ml_estimate = english_query_to_iql_posterior(
                data.english_query, data.genparse_url, data.grammar, data.grammar_path
            )
            map_particle = max(data.posterior, key=data.posterior.get).split('\n')[0].strip() + "\n"
            data.query = map_particle

    def select_best_dsl(data_structs):
        return sorted(data_structs, key=lambda x: x.log_ml_estimate, reverse=True)[0]

    english_prob_query = "what is the relationship between commute time and age?"
    score_query_dsls(english_prob_query)
    data = select_best_dsl(data_structs)
    print(data.grammar_path)
    # TODO: implement case to run cols query in `run_query`
    df = run_query(data.parser, data.interpreter, data.query, data.grammar_path)

    english_cols_query = "tell me what are variables related to education in this model?"

    # TODO: test once we have the correct grammar


if __name__ == "__main__":
    main()
