import requests
import json
from english_to_iql_demo.pre_prompt import pre_prompt_dispatch


def english_query_to_iql_posterior(user_query: str, genparse_url: str, grammar: str, pre_prompt: str) -> str:
    prompt = pre_prompt.format(user_query=user_query)
    request = {
        "prompt": prompt,
        "method": "smc-standard",
        "n_particles": 10,
        "lark_grammar": grammar,
        "proposal_name": "character",
        "proposal_args": {},
        "max_tokens": 100,
        "temperature": 1.
        }
    headers = {
        "Content-type": "application/json",
        "Accept": "application/json"
        }
    x = requests.post(genparse_url, json = request, headers=headers)

    response = json.loads(x.text)
    posterior = response['posterior']
    log_ml_estimate = response['log_ml_estimate']
    sorted_posterior = [
        {"query": k.strip(), "pval": v} 
        for k, v 
        in sorted(posterior.items(), key=lambda item: -item[1])
    ]
    return sorted_posterior, log_ml_estimate
