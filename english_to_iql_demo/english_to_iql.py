import requests
import urllib.parse
import json


def english_query_to_iql(user_query: str, genparse_url: str) -> str:
    request = {
        "prompt": user_query,
        "method": "smc-standard",
        "n_particles": 10,
        "grammar_name": "tiny_sql",
        "proposal_name": "character",
        "proposal_args": {},
        "max_tokens": 50
        }
    headers ={
        "Content-type": "application/json",
        "Accept": "application/json"
        }
    x = requests.post(genparse_url, json = request, headers=headers)

    response = json.loads(x.text)
    posterior = response['posterior']
    return max(posterior, key=posterior.get)