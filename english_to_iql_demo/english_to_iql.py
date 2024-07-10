import requests
import json
from english_to_iql_demo.pre_prompt import pre_prompt


def english_query_to_iql(user_query: str, genparse_url: str, grammar: str) -> str:
    prompt = pre_prompt.format(user_query=user_query)
    request = {
        "prompt": prompt,
        "method": "smc-standard",
        "n_particles": 10,
        "lark_grammar": grammar,
        "proposal_name": "character",
        "proposal_args": {},
        "max_tokens": 100,
        "temperature": 0.4
        }
    headers = {
        "Content-type": "application/json",
        "Accept": "application/json"
        }
    x = requests.post(genparse_url, json = request, headers=headers)

    response = json.loads(x.text)
    posterior = response['posterior']
    map_particle = max(posterior, key=posterior.get)
    # hack for unconstrained grammar
    map_particle = map_particle.split('\n')[0].strip() + "\n"
    return map_particle
