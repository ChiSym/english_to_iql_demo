from fastapi import FastAPI, Request, Form
from fastapi.responses import FileResponse
from english_to_iql_demo.english_to_iql import english_query_to_iql
from english_to_iql_demo.plot import plot_context_first_vars
from dataclasses import dataclass
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from jinja2_fragments.fastapi import Jinja2Blocks
from typing import Annotated
from english_to_iql_demo.clojure_interaction import get_iql_shell, iql_save
import pexpect


import shutil
import os


templates = Jinja2Blocks(directory="src")

default_dataset = "data/data_1000_sample.csv"
query_result_path = "results/iql_out.csv"

@dataclass
class Data:
    english_query: str
    iql_query: str
    iql: pexpect.pty_spawn.spawn


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Context manager for FastAPI app. It will run all code before `yield`
    on app startup, and will run code after `yeld` on app shutdown. This method
    runs a subprocess on app startup which is the equivalent of running the
    tailwindcss command `tailwindcss -i ./src/tw.css -o ./css/main.css`.

    Must be passed as a property of the FastAPI app. (app = FastAPI(lifespan=lifespan))
    """
    cwd = os.getcwd()
    shutil.copyfile(
        os.path.join(cwd, default_dataset), os.path.join(cwd, query_result_path)
    )


    # try:
    #     subprocess.call(
    #         f"tailwindcss -i {os.path.join(cwd, 'src/input.css')} -o {os.path.join(cwd, 'dist/output.css')}",
    #         shell=True,
    #     )
    # except Exception as e:
    #     raise RuntimeError from e
    yield


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="dist"), name="static")


data = Data(english_query="", iql_query="", iql=get_iql_shell())



@app.get("/")
async def root(request: Request):
    context = plot_context_first_vars(query_result_path)

    return templates.TemplateResponse(
        "index.html.jinja",
        {"request": request, **context},
    )


@app.post("/post_english_query")
async def post_english_query(request: Request, english_query: Annotated[str, Form()]):
    data.english_query = english_query
    data.iql_query = english_query_to_iql(data.english_query)

    return templates.TemplateResponse(
        "index.html.jinja",
        {"request": request, "iql_query": data.iql_query},
        block_name="iql_query",
    )


@app.post("/post_iql_query")
async def post_iql_query(request: Request, iql_query: Annotated[str, Form()]):
    data.iql_query = iql_query
    iql_save(data.iql, data.iql_query)

    context = plot_context_first_vars(query_result_path)

    return templates.TemplateResponse(
        "index.html.jinja", {"request": request, **context}, block_name="plot"
    )


@app.get("/query_result.csv", response_class=FileResponse)
async def get_query_result():
    return query_result_path