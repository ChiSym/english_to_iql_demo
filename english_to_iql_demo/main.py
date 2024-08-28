import logging as log
from dataclasses import dataclass
from fastapi import Request
from typing import Annotated, List
import traceback

import polars as pl
from lark import Lark

from english_to_iql_demo.english_to_iql import english_query_to_iql, sync_query_state, OOD_REPLY
from english_to_iql_demo.plot import plot_dispatch
from english_to_iql_demo.pre_prompt import pre_prompt_dispatch
from english_to_iql_demo.run_query import run_query, interpreter_dispatch, Interpreter

from chat_demo.chat_demo_server import ChatDemoServer


log.getLogger().setLevel(log.DEBUG)
log.getLogger("jax").setLevel(log.WARNING)
log.getLogger("asyncio").setLevel(log.WARNING)



@dataclass
class Data:
    english_query: str
    grammars: List[str]
    parsers: List[Lark]
    pre_prompts: List[str]
    genparse_urls: List[str]
    interpreters: List[Interpreter]
    sorted_posteriors: List[List[dict]]
    log_ml_estimates: List[float]
    iql_queries: List[str]
    iql_query: str
    df: pl.DataFrame
    current_dsl: str

def load_grammar(grammar_path):
    with open(f"grammars/{grammar_path}", "r", encoding="utf-8") as f:
        grammar_str = f.read()
    return grammar_str

grammar_paths = ["us_lpm_prob.lark", "us_lpm_cols.lark"]
indices = range(len(grammar_paths))
genparse_urls = [
    "http://34.31.182.25:8888/infer",
    # "http://34.122.30.137:8888/infer", 
    "http://35.225.217.118:8888/infer",
    ]
assert len(grammar_paths) == len(set(genparse_urls))

grammars = list(map(load_grammar, grammar_paths))
parsers = list(map(Lark, grammars))
pre_prompts = list(map(pre_prompt_dispatch, grammar_paths))
interpreters = list(map(interpreter_dispatch, grammar_paths))
default_df = pl.from_dict({"x": [0], "y": [0]})

data = Data(
    english_query="",
    grammars=grammars,
    parsers=parsers,
    pre_prompts=pre_prompts,
    genparse_urls=genparse_urls,
    interpreters=interpreters,
    sorted_posteriors=[[{"query": "", "pval": 1.0}] for _ in indices],
    log_ml_estimates=[-float("inf") for _ in indices],
    iql_queries=[""],
    iql_query="",
    df=default_df,
    current_dsl="OOD",
)

default_context = {"page_title": "GenParse/LPM demo",
                #    "extra_js_scripts": "<script goes here..."
                #    "extra_css": "<style goes here...",
                   "english_query_placeholder": "Ask a question in plain English",
                   "row_result_template": "row_result_lpm_demo.html.jinja", 
                   "query2_template": "query2_lpm_demo.html.jinja"}

templates = ChatDemoServer.get_templates("src")

async def post_english_query(request: Request, english_query: str, query_counter):
    data.english_query = english_query

    try:
        data.iql_queries = english_query_to_iql(data)
        log.debug(f"Returned {len(data.iql_queries)} queries")
        data.iql_query = data.iql_queries[0]["query"]

        return templates.TemplateResponse(
            "index.html.jinja",
            default_context |
            {"request": request, 
            "idnum": next(query_counter),
            "iql_query": data.iql_query, 
            "iql_queries": data.iql_queries},
            block_name="query2",
        )
    
    except Exception as e:
        log.error(f"Error converting English query (\"{english_query}\") to GenSQL: {e}")
        return templates.TemplateResponse(
            "index.html.jinja",
            default_context |
            {"request": request, 
             "idnum": next(query_counter),
             "iql_query": f"{e}",
             "iql_queries": [{"query": f"{e}", "pval": 0.999999}]
             },
            block_name="query2")


async def post_iql_query(request: Request, query_counter, **kwargs):
    form_data = await request.form()
    log.debug(f"post_iql_query form data: {form_data}")
    
    form_query = form_data.get('iql_query', '')
    if form_query != data.iql_query:
        sync_query_state(data, form_query)

    try:
        if (data.current_dsl == "OOD") or (form_query.strip() == OOD_REPLY):
            data.df = default_df
            context = plot_dispatch("OOD", data.df)
        else:
            data.df = run_query(data.parser, data.interpreter, form_query)
            context = plot_dispatch(data.current_dsl, data.df)
        
        return templates.TemplateResponse(
            "index.html.jinja", 
            default_context |
            {"request": request, 
            "english_query": form_data["english_query"], 
            "query2_html": form_data["iql_query"], 
            "query2_modified": form_data["query2_modified"], 
            "idnum": next(query_counter), 
            **context}, 
            block_name="plot"
        )
    
    except Exception as e:
        log.error(f"Error running GenSQL query: {e}")
        traceback.print_exception(e)
        return templates.TemplateResponse(
            "index.html.jinja",
            default_context |
            {"request": request, 
             "english_query": form_data["english_query"], 
             "query2_html": form_data["iql_query"], 
             "idnum": next(query_counter), 
             "error": f"{e}"},
            block_name="plot",
        )



server = ChatDemoServer(
    templates=templates, 
    default_context=default_context, 
    query1_callback=post_english_query, 
    query2_callback=post_iql_query
)
server.setup_routes() # Create the default routes
app = server.get_app() # Expose the app for uvicorn CLI
