import json
import requests
from concurrent.futures import ThreadPoolExecutor

import jax.numpy as jnp
from jax.nn import logsumexp


OOD_REPLY = "I can't answer that"
DSLs = ["LPM", "data"]


def english_query_to_iql(data):
    indices = range(len(data.grammars))
    def score_query_dsls(data):
        def score_query_dsl(idx):
            data.sorted_posteriors[idx], data.log_ml_estimates[idx] = english_query_to_iql_posterior(
                data.english_query, data.genparse_urls[idx], data.grammars[idx], data.pre_prompts[idx]
            )

        with ThreadPoolExecutor() as executor:
            executor.map(score_query_dsl, indices)

    def select_best_dsl(data):
        ood_probs = [[x['pval'] for x in post if x['query']==OOD_REPLY] for post in data.sorted_posteriors]
        if any(ood_probs):
            flat = [x[0] if x else 0 for x in ood_probs]
            return min(indices, key=lambda idx: flat[idx])
        return max(indices, key=lambda idx: data.log_ml_estimates[idx])

    score_query_dsls(data)
    idx = select_best_dsl(data)
    data.current_dsl = DSLs[idx]
    data.parser = data.parsers[idx]
    data.interpreter = data.interpreters[idx]
    return data.sorted_posteriors[idx]


def english_query_to_iql_posterior(user_query: str, genparse_url: str, grammar: str, pre_prompt: str) -> str:
    prompt = pre_prompt.format(user_query=user_query)
    request = {
        "prompt": prompt,
        "method": "smc-standard",
        "n_particles": 60,
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
    # print(response)
    posterior = response['posterior']
    sorted_posterior = [
        {"query": k.strip(), "pval": v} 
        for k, v 
        in sorted(posterior.items(), key=lambda item: -item[1])
    ]
    log_weights = [v for k,v in response['log_weights'].items() if k.strip()!=OOD_REPLY]
    log_ml_estimate = logsumexp(jnp.array(log_weights)) - jnp.log(len(log_weights))
    return sorted_posterior, log_ml_estimate

def sync_query_state(data, form_query):
    def set_ood():
        data.current_dsl = "OOD"
        data.iql_query = OOD_REPLY
        data.iql_queries = [data.iql_query]
    bos, eos = " ", "\n"
    query = bos + form_query.strip() + eos
    if form_query.strip() == OOD_REPLY:
        set_ood()
        return
    for idx, parser in enumerate(data.parsers):
        try:
            parser.parse(query)
            data.current_dsl = DSLs[idx]
            data.iql_query = form_query
            data.iql_queries = [data.iql_query]
            data.parser = parser
            data.interpreter = data.interpreters[idx]
            return
        except:
            pass
    set_ood()
