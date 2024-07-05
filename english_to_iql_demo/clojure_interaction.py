import requests
import urllib.parse
import json
import polars as pl


def iql_run(iql_url, query):
    url = urllib.parse.urljoin(iql_url, "/api/query")

    request = {"query": query}
    headers ={
        "Content-type": "application/json",
        "Accept": "application/json"
        }
    x = requests.post(url, json = request, headers = headers)
    x.raise_for_status()

    # # ipdb.set_trace()
    # print(f"Response: {x.text}")

    response = json.loads(x.text)
    df = pl.from_dicts(response['rows'])
    return df.drop_nulls()
