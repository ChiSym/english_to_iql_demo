import logging as log
from dataclasses import dataclass
from itertools import count
from typing import Annotated, List

import polars as pl
from lark import Lark
from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from jinja2_fragments.fastapi import Jinja2Blocks

from english_to_iql_demo.english_to_iql import english_query_to_iql, OOD_REPLY
from english_to_iql_demo.plot import plot
from english_to_iql_demo.pre_prompt import pre_prompt_dispatch
from english_to_iql_demo.run_query import run_query, interpreter_dispatch, Interpreter

log.getLogger().setLevel(log.DEBUG)
log.getLogger("jax").setLevel(log.WARNING)
log.getLogger("asyncio").setLevel(log.WARNING)


templates = Jinja2Blocks(directory="src")
query_counter = count(1)
app = FastAPI()
app.mount("/static", StaticFiles(directory="dist"), name="static")

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
    queries: List[str]
    df: pl.DataFrame

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
    sorted_posteriors=[[{"query": "", "pval": 1.0}] for _ in indices],
    log_ml_estimates=[-float("inf") for _ in indices],
    queries=["" for _ in indices],
    df=pl.DataFrame(),
)

@app.get("/")
async def root(request: Request):
    context = plot(pl.DataFrame())

    return templates.TemplateResponse(
        "index.html.jinja",
        {"request": request, 
         "idnum": next(query_counter),
         "root": True,
        **context},
    )


@app.post("/post_english_query")
async def post_english_query(request: Request, english_query: Annotated[str, Form()]):
    data.english_query = english_query

    try:
        data.iql_queries = english_query_to_iql(data)
        data.iql_query = data.iql_queries[0]["query"]
    except Exception as e:
        log.error(f"Error converting English query (\"{english_query}\") to GenSQL: {e}")
        return templates.TemplateResponse(
            "index.html.jinja",
            {"request": request, 
             "idnum": next(query_counter),
             "iql_query": f"{e}",
             "iql_queries": [{"query": f"{e}", "pval": 0.999999}]
             },
            block_name="iql_query")

    return templates.TemplateResponse(
        "index.html.jinja",
        {"request": request, 
         "idnum": next(query_counter),
         "iql_query": data.iql_query, 
         "iql_queries": data.iql_queries},
        block_name="iql_query",
    )

@app.post("/post_iql_query")
async def post_iql_query(request: Request):
    form_data = await request.form()
    log.debug(f"/post_iql_query form data: {form_data}")
    
    if form_data.get('iql_query', '') != '':
        data.query = form_data.get('iql_query', '')

    try:
        assert data.query!=OOD_REPLY # TODO: need to handle case when can't answer and returns generic OOD reply
        data.df = run_query(data.parser, data.interpreter, form_data.get('iql_query', ''))
        assert isinstance(data.df, pl.DataFrame) # TODO: need to handle processing of column datadict output
    except Exception as e:
        log.error(f"Error running GenSQL query: {e}")
        return templates.TemplateResponse(
            "index.html.jinja",
            {"request": request, 
             "english_query": form_data["english_query"], 
             "gensql_query": form_data["iql_query"], 
             "idnum": next(query_counter), 
             "error": f"{e}"},
            block_name="plot",
        )

    return templates.TemplateResponse(
        "index.html.jinja", 
        {"request": request, 
         "english_query": form_data["english_query"], 
         "gensql_query": form_data["iql_query"], 
         "idnum": next(query_counter), 
         **context}, 
        block_name="plot"
    )