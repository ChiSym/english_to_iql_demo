from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from jinja2_fragments.fastapi import Jinja2Blocks
from typing import Annotated
from itertools import count

import json
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

physician_fields = [
    "first",
	"last",
    "specialty", 
    "npi",
    "school",
	"degree"
    ]
business_fields = [
    "legal_name",
    "addr",
    "addr2",
    "city",
    "zip",
    ]

templates = Jinja2Blocks(directory="src")
query_counter = count(1)

app = FastAPI()
app.mount("/static", StaticFiles(directory="dist"), name="static")

@app.get("/")
async def root(request: Request):
    context = {} 

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

        # log.debug(f"pclean response: {pclean_resp}")

        extracted_results = extract_docs_and_biz(pclean_resp)
        docs, biz, doc_keys, biz_keys = extracted_results.values()
        doc_keys = physician_fields + list(doc_keys - set(physician_fields))
        biz_keys = business_fields + list(biz_keys - set(business_fields))
        
        # combined = pclean_resp["results"]
        # combined.sort(key=lambda x: x["count"], reverse=True)
        # normalize_counts(combined)

        sample_count = pclean_resp["count"]
        not_found_pval = 1 # (sample_count - entities_count(combined)) / sample_count

        return templates.TemplateResponse(
            "genfact.html.jinja",
            {"request": request, 
            "idnum": next(query_counter),
            "physician_fields": physician_fields,
            "business_fields": business_fields,
            "english_query": english_query,
            "genfact_entity": genfact_entity,
            "not_found_pval": not_found_pval,
            "docs": docs,
            "biz": biz,
            "doc_keys": doc_keys,
            "biz_keys": biz_keys,
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

def pclean_row_response(*, pclean_resp: dict, request, english_query, genfact_entity):
    # log.debug(f"pclean response: {pclean_resp}")

    extracted_results = extract_docs_and_biz(pclean_resp)
    docs, biz, doc_keys, biz_keys = extracted_results.values()
    doc_keys = physician_fields + list(doc_keys - set(physician_fields))
    biz_keys = business_fields + list(biz_keys - set(business_fields))
    
    sample_count = pclean_resp["count"]
    not_found_pval = 1 # (sample_count - entities_count(combined)) / sample_count

    return templates.TemplateResponse(
        "genfact.html.jinja",
        {"request": request, 
        "idnum": next(query_counter),
        "physician_fields": physician_fields,
        "business_fields": business_fields,
        "english_query": english_query,
        "genfact_entity": genfact_entity,
        "not_found_pval": not_found_pval,
        "docs": docs,
        "biz": biz,
        "doc_keys": doc_keys,
        "biz_keys": biz_keys,
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
            

    # Sort the dicts' values by the "count" field for the histograms
    sorted_docs = sorted(docs.values(), key=lambda x: x["count"], reverse=True)
    sorted_biz = sorted(biz.values(), key=lambda x: x["count"], reverse=True)

    normalize_counts(sorted_docs)
    normalize_counts(sorted_biz)

    # print(f"docs: {docs}")
    # print(">>>>>>>")
    # print(f"biz: {biz}")
    # print(f"sorted biz {sorted_biz}")
    # print(f"doc keys: {doc_keys}")
    # print(">>>>>>>")
    # print(f"biz keys: {biz_keys}")
    return {"docs": sorted_docs, "biz": sorted_biz, "doc_keys": doc_keys, "biz_keys": biz_keys}

def entities_count(entities: list) -> int:
    return sum([ent["count"] for ent in entities])

def normalize_counts(entities: list) -> None:
    log.debug(f"normalizing entities entities: {entities}")
    total_count = entities_count(entities)
    log.debug(f"total entities count: {total_count}")
    for ent in entities:
        ent["proportion"] = ent["count"] / total_count



@app.post("/post_pclean_dummy")
async def post_pclean_dummy(request: Request, empty: bool = True):
    if empty:
        pclean_resp = {
            "businesses_count": 1000,
            "business_histogram": {},
            "physician_new_entity": 1000,
            "physicians": [],
            "businesses": [],
            "count": 1000,
            "business_new_entity": 1000,
            "results": [],
            "physician_count": 1000,
            "physician_histogram": {}
        }
    else:
        pclean_resp = {
            "businesses_count": 1000,
            "business_histogram": {
                "row_47052": 9,
                "row_45941": 9,
                "row_47027": 9,
                "row_44323": 16,
                "row_47572": 8,
                "row_45389": 8,
                "row_48339": 11,
                "row_46760": 7
            },
            "physician_new_entity": 0,
            "physicians": [{
                "id": "row_6197",
                "count": 1000,
                "entity": {
                    "specialty": "DIAGNOSTIC RADIOLOGY",
                    "npi": 1124012851,
                    "school": "ALBANY MEDICAL COLLEGE OF UNION UNIVERSITY",
                    "first": "STEVEN",
                    "degree": "MD",
                    "last": "GILMAN"
                }
            }],
            "businesses": [{
                "id": "row_46760",
                "count": 7,
                "entity": {
                    "addr": "126 W CHURCH ST",
                    "addr2": "",
                    "city": "DILLSBURG",
                    "zip": "170191280",
                    "legal_name": "SPIRIT PHYSICIAN SERVICES INC"
                }
            }, {
                "id": "row_48339",
                "count": 11,
                "entity": {
                    "addr": "126 W CHURCH ST",
                    "addr2": "SUITE 200",
                    "city": "DILLSBURG",
                    "zip": "170191280",
                    "legal_name": "SPIRIT PHYSICIAN SERVICES INC"
                }
            }, {
                "id": "row_47052",
                "count": 9,
                "entity": {
                    "addr": "20 CAPITAL DR",
                    "addr2": "",
                    "city": "HARRISBURG",
                    "zip": "171109446",
                    "legal_name": "SPIRIT PHYSICIAN SERVICES INC"
                }
            }, {
                "id": "row_44323",
                "count": 16,
                "entity": {
                    "addr": "429 N 21ST ST",
                    "addr2": "",
                    "city": "CAMP HILL",
                    "zip": "170112202",
                    "legal_name": "SPIRIT PHYSICIAN SERVICES INC"
                }
            }, {
                "id": "row_47572",
                "count": 8,
                "entity": {
                    "addr": "4665 E TRINDLE RD",
                    "addr2": "",
                    "city": "MECHANICSBURG",
                    "zip": "170503640",
                    "legal_name": "SPIRIT PHYSICIAN SERVICES INC"
                }
            }, {
                "id": "row_45389",
                "count": 8,
                "entity": {
                    "addr": "431 N 21ST ST",
                    "addr2": "",
                    "city": "CAMP HILL",
                    "zip": "170112202",
                    "legal_name": "SPIRIT PHYSICIAN SERVICES INC"
                }
            }, {
                "id": "row_45941",
                "count": 9,
                "entity": {
                    "addr": "1211 FORGE RD",
                    "addr2": "",
                    "city": "CARLISLE",
                    "zip": "170133183",
                    "legal_name": "SPIRIT PHYSICIAN SERVICES INC"
                }
            }, {
                "id": "row_47027",
                "count": 9,
                "entity": {
                    "addr": "2313 OAKFIELD RD",
                    "addr2": "",
                    "city": "WARRINGTON",
                    "zip": "189762010",
                    "legal_name": "SPIRIT PHYSICIAN SERVICES INC"
                }
            }],
            "count": 1000,
            "business_new_entity": 923,
            "results": [{
                "ids": ["row_6197", "row_46760"],
                "count": 7,
                "physician": {
                    "specialty": "DIAGNOSTIC RADIOLOGY",
                    "npi": 1124012851,
                    "school": "ALBANY MEDICAL COLLEGE OF UNION UNIVERSITY",
                    "first": "STEVEN",
                    "degree": "MD",
                    "last": "GILMAN"
                },
                "business": {
                    "addr": "126 W CHURCH ST",
                    "addr2": "",
                    "city": "DILLSBURG",
                    "zip": "170191280",
                    "legal_name": "SPIRIT PHYSICIAN SERVICES INC"
                }
            }, {
                "ids": ["row_6197", "row_48339"],
                "count": 11,
                "physician": {
                    "specialty": "DIAGNOSTIC RADIOLOGY",
                    "npi": 1124012851,
                    "school": "ALBANY MEDICAL COLLEGE OF UNION UNIVERSITY",
                    "first": "STEVEN",
                    "degree": "MD",
                    "last": "GILMAN"
                },
                "business": {
                    "addr": "126 W CHURCH ST",
                    "addr2": "SUITE 200",
                    "city": "DILLSBURG",
                    "zip": "170191280",
                    "legal_name": "SPIRIT PHYSICIAN SERVICES INC"
                }
            }, {
                "ids": ["row_6197", "row_47052"],
                "count": 9,
                "physician": {
                    "specialty": "DIAGNOSTIC RADIOLOGY",
                    "npi": 1124012851,
                    "school": "ALBANY MEDICAL COLLEGE OF UNION UNIVERSITY",
                    "first": "STEVEN",
                    "degree": "MD",
                    "last": "GILMAN"
                },
                "business": {
                    "addr": "20 CAPITAL DR",
                    "addr2": "",
                    "city": "HARRISBURG",
                    "zip": "171109446",
                    "legal_name": "SPIRIT PHYSICIAN SERVICES INC"
                }
            }, {
                "ids": ["row_6197", "row_44323"],
                "count": 16,
                "physician": {
                    "specialty": "DIAGNOSTIC RADIOLOGY",
                    "npi": 1124012851,
                    "school": "ALBANY MEDICAL COLLEGE OF UNION UNIVERSITY",
                    "first": "STEVEN",
                    "degree": "MD",
                    "last": "GILMAN"
                },
                "business": {
                    "addr": "429 N 21ST ST",
                    "addr2": "",
                    "city": "CAMP HILL",
                    "zip": "170112202",
                    "legal_name": "SPIRIT PHYSICIAN SERVICES INC"
                }
            }, {
                "ids": ["row_6197", "row_47572"],
                "count": 8,
                "physician": {
                    "specialty": "DIAGNOSTIC RADIOLOGY",
                    "npi": 1124012851,
                    "school": "ALBANY MEDICAL COLLEGE OF UNION UNIVERSITY",
                    "first": "STEVEN",
                    "degree": "MD",
                    "last": "GILMAN"
                },
                "business": {
                    "addr": "4665 E TRINDLE RD",
                    "addr2": "",
                    "city": "MECHANICSBURG",
                    "zip": "170503640",
                    "legal_name": "SPIRIT PHYSICIAN SERVICES INC"
                }
            }, {
                "ids": ["row_6197", "row_45389"],
                "count": 8,
                "physician": {
                    "specialty": "DIAGNOSTIC RADIOLOGY",
                    "npi": 1124012851,
                    "school": "ALBANY MEDICAL COLLEGE OF UNION UNIVERSITY",
                    "first": "STEVEN",
                    "degree": "MD",
                    "last": "GILMAN"
                },
                "business": {
                    "addr": "431 N 21ST ST",
                    "addr2": "",
                    "city": "CAMP HILL",
                    "zip": "170112202",
                    "legal_name": "SPIRIT PHYSICIAN SERVICES INC"
                }
            }, {
                "ids": ["row_6197", "row_45941"],
                "count": 9,
                "physician": {
                    "specialty": "DIAGNOSTIC RADIOLOGY",
                    "npi": 1124012851,
                    "school": "ALBANY MEDICAL COLLEGE OF UNION UNIVERSITY",
                    "first": "STEVEN",
                    "degree": "MD",
                    "last": "GILMAN"
                },
                "business": {
                    "addr": "1211 FORGE RD",
                    "addr2": "",
                    "city": "CARLISLE",
                    "zip": "170133183",
                    "legal_name": "SPIRIT PHYSICIAN SERVICES INC"
                }
            }, {
                "ids": ["row_6197", "row_47027"],
                "count": 9,
                "physician": {
                    "specialty": "DIAGNOSTIC RADIOLOGY",
                    "npi": 1124012851,
                    "school": "ALBANY MEDICAL COLLEGE OF UNION UNIVERSITY",
                    "first": "STEVEN",
                    "degree": "MD",
                    "last": "GILMAN"
                },
                "business": {
                    "addr": "2313 OAKFIELD RD",
                    "addr2": "",
                    "city": "WARRINGTON",
                    "zip": "189762010",
                    "legal_name": "SPIRIT PHYSICIAN SERVICES INC"
                }
            }],
            "physician_count": 1000,
            "physician_histogram": {
                "row_6197": 1000
            }
        }

    return pclean_row_response(pclean_resp=pclean_resp, request=request, english_query="dummy", genfact_entity="dummy")