import logging as log
from dataclasses import dataclass
from fastapi import Request
from typing import Annotated, List
import traceback

import polars as pl
from lark import Lark

from english_to_iql_demo.english_to_iql import english_query_to_iql, sync_query_state, OOD_REPLY
from english_to_iql_demo.plot import plot_cols, plot_lpm, plot_ood, plot_geo
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
                   "query1_template": "query1_lpm_demo.html.jinja",
                   "query2_template": "query2_lpm_demo.html.jinja",
                   "extra_query1_form_attrs": 'hx-encoding="multipart/form-data"'}

templates = ChatDemoServer.get_templates("src")

async def post_english_query(request: Request, english_query: str, query_counter):
    try:
        form_data = dict(await request.form())

        # Check if 'file' is in the form data
        if 'file' in form_data:
            file = form_data['file']
            log.debug(f"File info:")
            log.debug(f"  Filename: {file.filename}")
            log.debug(f"  Content type: {file.content_type}")
            log.debug(f"  File size: {len(file.file.read())} bytes")
            # Reset the file pointer to the beginning
            file.file.seek(0)

            # TODO: Something with the file
        else:
            log.debug("No file was uploaded in this request.")

        data.english_query = english_query
        data.iql_queries = english_query_to_iql(data)
        # log.debug(f"Returned {len(data.iql_queries)} queries")
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

    form_query = form_data.get('iql_query', '')
    if form_query != data.iql_query:
        sync_query_state(data, form_query)

    try:
        match data.current_dsl:
            case "OOD":
                data.df = default_df
                context = plot_ood(data.df)
            case "LPM":
                query_schema, data.df = run_query(data.parser, data.interpreter, form_query)
                if query_schema == "geo":
                    context = plot_geo(data.df)
                else:
                    context = plot_lpm(data.df, query_schema)
            case "data":
                data.df = run_query(data.parser, data.interpreter, form_query)
                context = plot_cols(data.df)
            case _:
                raise log.error(f"Invalid DSL: {data.current_dsl}")

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
