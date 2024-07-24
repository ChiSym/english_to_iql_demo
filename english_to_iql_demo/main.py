from fastapi import FastAPI, Request, Form
from english_to_iql_demo.plot import plot
from fastapi.staticfiles import StaticFiles
from jinja2_fragments.fastapi import Jinja2Blocks
from typing import Annotated
from itertools import count


import json
import polars as pl
import logging as log
import requests

import http.client as http_client
import traceback

log.getLogger().setLevel(log.DEBUG)
log.getLogger("jax").setLevel(log.WARNING)
log.getLogger("asyncio").setLevel(log.WARNING)
log.getLogger("multipart.multipart").setLevel(log.WARNING)

def log_http_output():
    '''Log HTTP input/output to the console'''
    http_client.HTTPConnection.debuglevel = 1

    log.basicConfig()
    log.getLogger().setLevel(log.DEBUG)
    requests_log = log.getLogger("requests.packages.urllib3")
    requests_log.setLevel(log.DEBUG)
    requests_log.propagate = True
log_http_output()

genfact_server = '34.44.35.203'
genfact_server_port = 8888

templates = Jinja2Blocks(directory="src")
query_counter = count(1)

app = FastAPI()
app.mount("/static", StaticFiles(directory="dist"), name="static")

@app.get("/")
async def root(request: Request):
    context = plot(pl.DataFrame())

    return templates.TemplateResponse(
        "genfact.html.jinja",
        {"request": request, 
         "idnum": next(query_counter),
         "root": True,
        **context},
    )


@app.post("/post_genfact_query")
async def post_genfact_query(request: Request, english_query: Annotated[str, Form()]):
    genfact_url = f"http://{genfact_server}:{genfact_server_port}/sentence-to-doctor-data"

    try:
        response = requests.post(genfact_url, 
                                 json={"sentence": english_query},
                                 timeout=90.0)

        log.debug(f"GenFact response: {response.json()}")

        entities = [{'entity_html': k, 'pval': v['likelihood'], **v} for k, v in response.json()['posterior'].items()]
        # Remove key/value pairs where the value is 'NONE' from the 'as_object' property
        for entity in entities:
            if 'as_object' in entity:
                entity['as_object'] = {k: v for k, v in entity['as_object'].items() if v != 'NONE'}
        entities.sort(key=lambda x: x['pval'], reverse=True)

        return templates.TemplateResponse(
            "genfact.html.jinja",
            {"request": request, 
            "idnum": next(query_counter),
            "ml_entity": entities[0],
            "genfact_entities": entities},
            block_name="query2",
        )
        
    except Exception as e:
        log.error(f"Error in GenParse on English query (\"{english_query}\") : {e}")
        return templates.TemplateResponse(
            "genfact.html.jinja",
            {"request": request, 
             "idnum": next(query_counter),
             "ml_entity": None,
             "genfact_entities": [],
             "error": f"{e}"
             },
            block_name="query2")

    
@app.post("/post_pclean_query")
async def post_pclean_query(request: Request, 
                            english_query: Annotated[str, Form()], 
                            genfact_entity: Annotated[str, Form()]):
    try:
        genfact_url = f"http://{genfact_server}:{genfact_server_port}/run-pclean"

        # log.debug(f"genfact_entity: {genfact_entity}")

        genfact_entity_dict = json.loads(genfact_entity)
        pclean_payload = {"observations": genfact_entity_dict}
        if 'c2z3' in pclean_payload['observations']:
            del pclean_payload['observations']['c2z3']
        # log.debug(f"pclean payload: {pclean_payload}")

        response = requests.post(genfact_url, json=pclean_payload, timeout=90.0)
        pclean_resp = response.json()

        extracted_results = extract_docs_and_biz(pclean_resp)
        
        combined = pclean_resp["results"]
        combined.sort(key=lambda x: x["count"], reverse=True)
        normalize_counts(combined)

        return templates.TemplateResponse(
            "genfact.html.jinja",
            {"request": request, 
            "idnum": next(query_counter),
            "english_query": english_query,
            "genfact_entity": genfact_entity,
            "combined": combined,
            **extracted_results,
            },
            block_name="plot")
    
    except Exception as e:
        log.error(f"Error running pclean for genfact_entity (\"{genfact_entity}\") : {e}")
        traceback.print_exception(e)
        return templates.TemplateResponse(
            "genfact.html.jinja",
            {"request": request, 
             "idnum": next(query_counter),
             "genfact_entity": genfact_entity,
             "error": f"{e}"
             },
            block_name="plot")


def extract_docs_and_biz(pclean_result: dict) -> dict:
    docs = {}
    biz = {}
    doc_keys = set()
    biz_keys = set()

    # Extract docs/biz into maps, avoiding dupes
    for combined_result in pclean_result["results"]:
        doc_id = combined_result["ids"][0]
        biz_id = combined_result["ids"][1]

        if doc_id not in docs:
            docs[doc_id] = combined_result["physician"]
            doc_keys |= set(docs[doc_id].keys())
            docs[doc_id]["id"] = doc_id
            docs[doc_id]["count"] = pclean_result["physician_histogram"][doc_id]
            
        if biz_id not in biz:
            biz[biz_id] = combined_result["business"]
            biz_keys |= set(biz[biz_id].keys())
            biz[biz_id]["id"] = biz_id
            biz[biz_id]["count"] = pclean_result["business_histogram"][biz_id]
            
    # normalize_counts(docs)
    # normalize_counts(biz)

    # Sort the dicts' values by the "count" field for the histograms
    sorted_docs = sorted(docs.values(), key=lambda x: x["count"], reverse=True)
    sorted_biz = sorted(biz.values(), key=lambda x: x["count"], reverse=True)

    normalize_counts(sorted_docs)
    normalize_counts(sorted_biz)

    # print(f"docs: {docs}")
    # print(">>>>>>>")
    # print(f"biz: {biz}")
    print(f"sorted biz {sorted_biz}")
    # print(f"doc keys: {doc_keys}")
    # print(">>>>>>>")
    # print(f"biz keys: {biz_keys}")
    return {"docs": sorted_docs, "biz": sorted_biz, "doc_keys": doc_keys, "biz_keys": biz_keys}

# def normalize_counts(entities: dict) -> None:
#     log.debug(f"normalizing entities: {entities}")
#     total_count = sum([ent["count"] for ent in entities.values()])
#     log.debug(f"total count: {total_count}")
#     for id, ent in entities.items():
#         ent["proportion"] = ent["count"] / total_count

# def normalize_combined_counts(combined: list) -> None:
#     log.debug(f"normalizing combined entities: {combined}")
#     total_count = sum([ent["count"] for ent in combined])
#     log.debug(f"total combined count: {total_count}")
#     for ent in combined:
#         ent["proportion"] = ent["count"] / total_count

def normalize_counts(entities: list) -> None:
    log.debug(f"normalizing entities entities: {entities}")
    total_count = sum([ent["count"] for ent in entities])
    log.debug(f"total entities count: {total_count}")
    for ent in entities:
        ent["proportion"] = ent["count"] / total_count