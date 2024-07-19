from fastapi import FastAPI, Request, Form
from english_to_iql_demo.english_to_iql import english_query_to_iql
from english_to_iql_demo.plot import plot
from dataclasses import dataclass
from fastapi.staticfiles import StaticFiles
from jinja2_fragments.fastapi import Jinja2Blocks
from typing import Annotated
from english_to_iql_demo.run_query import run_query
from jax_multimix.interpreter import Interpreter
from lark import Lark
from itertools import count
from jax_multimix.model import mixture_model
from jax_multimix.model import SumProductInference


import pickle
import polars as pl
import logging as log


log.getLogger().setLevel(log.DEBUG)

templates = Jinja2Blocks(directory="src")
query_counter = count(1)

@dataclass
class Data:
    english_query: str
    genparse_url: str
    query: str
    grammar: str
    parser: Lark
    interpreter: Interpreter
    df: pl.DataFrame

app = FastAPI()
app.mount("/static", StaticFiles(directory="dist"), name="static")

with open("us_lpm_grammar.lark", "r") as f:
    lark_grammar_str = f.read()

parser = Lark(lark_grammar_str)

grammar = lark_grammar_str
# grammar = "start: /.+/"

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
    query="", 
    genparse_url="http://34.122.30.137:8888/infer",
    parser=parser,
    interpreter=interpreter,
    grammar=grammar,
    df = pl.DataFrame()
    )



@app.get("/")
async def root(request: Request):
    context = plot(data.df)

    return templates.TemplateResponse(
        "index.html.jinja",
        {"request": request, 
         "idnum": next(query_counter),
        **context},
    )


@app.post("/post_english_query")
async def post_english_query(request: Request, english_query: Annotated[str, Form()]):
    data.english_query = english_query

    try:
        data.iql_queries = english_query_to_iql(
            data.english_query,
            data.genparse_url,
            data.grammar,
            )
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
        data.df = run_query(data.parser, data.interpreter, form_data.get('iql_query', ''))
        context = plot(data.df)
        
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