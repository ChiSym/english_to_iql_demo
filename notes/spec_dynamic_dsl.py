import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Dict, List, Union

from lark import Lark
import polars as pl

from english_to_iql_demo.pre_prompt import pre_prompt_dispatch
from english_to_iql_demo.english_to_iql import english_query_to_iql_posterior
from english_to_iql_demo.run_query import run_query, interpreter_dispatch, Interpreter

@dataclass
class Data:
    english_query: str
    grammars: List[str]
    parsers: List[Lark]
    pre_prompts: List[str]
    genparse_urls: List[str]
    interpreters: List[Interpreter]
    sorted_posteriors: List[Dict[str, Union[str, float]]]
    log_ml_estimates: List[float]
    queries: List[str]
    df: pl.DataFrame



def main():

    def load_grammar(grammar_path):
        with open(f"grammars/{grammar_path}", "r", encoding="utf-8") as f:
            grammar_str = f.read()
        return grammar_str

    grammar_paths = ["us_lpm_prob.lark", "us_lpm_cols.lark"]
    indices = range(len(grammar_paths))
    genparse_urls = ["http://34.122.30.137:8888/infer" for _ in indices] # TODO: add 2nd endpoint for the column DSL
    assert len(grammar_paths) == len(genparse_urls)

    grammars = list(map(load_grammar, grammar_paths))
    parsers = list(map(Lark, grammars))
    pre_prompts = list(map(pre_prompt_dispatch, grammar_paths))
    interpreters = list(map(interpreter_dispatch, grammar_paths))

    data = Data(
        english_query="",
        grammars=grammars,
        parsers=parsers,
        pre_prompts=pre_prompts,
        genparse_urls=genparse_urls,
        interpreters=interpreters,
        sorted_posteriors=[{} for _ in indices],
        log_ml_estimates=[-float("inf") for _ in indices],
        queries=["" for _ in indices],
        df=pl.DataFrame(),
    )

    def run_query_using_best_dsl(data):
        def score_query_dsls(data):
            def score_query_dsl(idx):
                data.sorted_posteriors[idx], data.log_ml_estimates[idx] = english_query_to_iql_posterior(
                    data.english_query, data.genparse_urls[idx], data.grammars[idx], data.pre_prompts[idx]
                )
                map_particle = data.sorted_posteriors[idx][0]["query"]
                data.queries[idx] = map_particle

            with ThreadPoolExecutor() as executor:
                executor.map(score_query_dsl, indices)
            assert all(data.queries), "Failure in scoring queries"

        def select_best_dsl(data):
            options = [idx for idx in indices if data.queries[idx]!="I can't answer that"]
            if not options:
                return -1
            return max(options, key=lambda idx: data.log_ml_estimates[idx])

        score_query_dsls(data)
        idx = select_best_dsl(data)
        if idx == -1:
            return "Sorry, I can't answer that. Could you try again?"
        out = run_query(data.parsers[idx], data.interpreters[idx], data.queries[idx])
        return out


    def test_run_query_using_best_dsl(english_query):
        data.english_query = english_query
        out = run_query_using_best_dsl(data)
        print("TESTING THE FOLLOWING QUERY:")
        print(data.english_query)
        print("DSL SCORES:")
        print(json.dumps({log_ml: query for log_ml, query in zip(data.log_ml_estimates, data.queries)}, indent=2))
        print("DISPATCHED DSL OUTPUT:")
        if isinstance(out, pl.DataFrame):
            print(out)
        else:
            print(json.dumps(out, indent=2))

    test_run_query_using_best_dsl("What is the relationship between commute time and age?")
    test_run_query_using_best_dsl("Tell me what are some variables in this model relevant for religion?")
    test_run_query_using_best_dsl("What is the color blue?")


if __name__ == "__main__":
    main()
