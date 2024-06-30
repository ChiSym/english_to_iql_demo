from fastapi import FastAPI, Request, Form
from fastapi.responses import FileResponse
from english_to_iql_demo.english_to_iql import english_query_to_iql
from english_to_iql_demo.plot import plot_context_first_vars
from dataclasses import dataclass
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from jinja2_fragments.fastapi import Jinja2Blocks
from typing import Annotated
from english_to_iql_demo.clojure_interaction import iql_save

import shutil
import os


templates = Jinja2Blocks(directory="src")

default_dataset = "data/data_1000_sample.csv"
query_result_path = "results/iql_out.csv"

@dataclass
class Data:
    english_query: str
    genparse_url: str
    iql_query: str
    iql_url: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Context manager for FastAPI app. It will run all code before `yield`
    on app startup, and will run code after `yield` on app shutdown. This method
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

data = Data(
    english_query="", 
    iql_query="", 
    # iql_url="http://34.45.8.32:3000/",
    iql_url="http://localhost:8888/",
    genparse_url="http://34.122.30.137:8888/infer",
    )


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
    data.iql_query = english_query_to_iql(
        data.english_query,
        data.genparse_url,
        )

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

    # this post request is triggering twice, 
    # using this hack to get around it
    if form_data.get('iql_query', '') != '':
        data.iql_query = form_data.get('iql_query', '')
    
    iql_save(data.iql_url, data.iql_query)

    context = plot_context_first_vars(query_result_path)

    return templates.TemplateResponse(
        "index.html.jinja", {"request": request, **context}, block_name="plot"
    )


@app.get("/query_result.csv", response_class=FileResponse)
async def get_query_result():
    return query_result_path