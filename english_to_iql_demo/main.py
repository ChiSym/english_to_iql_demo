from fastapi import FastAPI, Request, Form
from fastapi.responses import FileResponse
from english_to_iql_demo.english_to_iql import english_query_to_iql
from english_to_iql_demo.plot import plot
from dataclasses import dataclass
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from jinja2_fragments.fastapi import Jinja2Blocks
from typing import Annotated
from english_to_iql_demo.clojure_interaction import iql_run
from itertools import count
import requests

import polars as pl
import shutil
import os
import logging as log


log.getLogger().setLevel(log.DEBUG)

templates = Jinja2Blocks(directory="src")
query_counter = count(1)

@dataclass
class Data:
    english_query: str
    genparse_url: str
    iql_query: str
    iql_url: str
    grammar: str
    df: pl.DataFrame

app = FastAPI()
app.mount("/static", StaticFiles(directory="dist"), name="static")

with open("tiny_iql.lark", "r") as f:
    grammar = f.read()

data = Data(
    english_query="", 
    iql_query="", 
    iql_url="http://34.45.8.32:3000/",
    # iql_url="http://localhost:8888/",
    genparse_url="http://34.122.30.137:8888/infer",
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
        data.iql_query = english_query_to_iql(
            data.english_query,
            data.genparse_url,
            data.grammar,
            )
    except Exception as e:
        log.error(f"Error converting English query to GenSQL: {e}")
        return templates.TemplateResponse(
            "index.html.jinja",
            {"request": request, 
             "iql_query": f"{e}"},
            block_name="iql_query")

    return templates.TemplateResponse(
        "index.html.jinja",
        {"request": request, "iql_query": data.iql_query},
        block_name="iql_query",
    )

# @app.post("/update_iql_query")
# async def update_iql_query(request: Request):
#     form_data = await request.form()
#     data.iql_query = form_data['iql_query']
#     print(form_data)
#     return data.iql_query


# @app.post("/post_iql_query")
# async def post_iql_query(request: Request):
#     # note: commented the lines below because there the 'iql_query' property
#     # seemed to be empty, but this might remove the capacity to manually
#     # edit the query
#     # iql_query = request.headers['iql_query']
#     # iql_query = urllib.parse.unquote(iql_query)
#     # data.iql_query = re.sub("\s\s+" , " ", iql_query)
#     iql_save(data.iql_url, data.iql_query)

#     context = plot_context_first_vars(query_result_path)

#     return templates.TemplateResponse(
#         "index.html.jinja", {"request": request, **context}, block_name="plot"
#     )

@app.post("/post_iql_query")
async def post_iql_query(request: Request):
    form_data = await request.form()
    log.debug(f"/post_iql_query form data: {form_data}")
    
    if form_data.get('iql_query', '') != '':
        data.iql_query = form_data.get('iql_query', '')

    try:
        data.df = iql_run(data.iql_url, form_data.get('iql_query', ''))
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

    context = plot(data.df)

    return templates.TemplateResponse(
        "index.html.jinja", 
        {"request": request, 
         "english_query": form_data["english_query"], 
         "gensql_query": form_data["iql_query"], 
         "idnum": next(query_counter), 
         **context}, 
        block_name="plot"
    )

