import requests
import urllib.parse
import json
import polars as pl

def iql_save(iql_url, query, outfile="results/iql_out.csv"):
    df = iql_run(iql_url, query)
    df.write_csv(outfile)

def iql_run(iql_url, query):
    url = urllib.parse.urljoin(iql_url, "/api/query")

    request = {"query": query}
    headers ={
        "Content-type": "application/json",
        "Accept": "application/json"
        }
    x = requests.post(url, json = request, headers=headers)

    response = json.loads(x.text)
    df = pl.from_dicts(response['rows'])

    return df