import json
import requests
from concurrent.futures import ThreadPoolExecutor


OOD_REPLY = "Sorry, I can't answer that. Could you try again?"
DSLs = ["LPM", "data"] + ["OOD"] # if updating, OOD must remain last


def english_query_to_iql(data):
    indices = range(len(data.grammars))
    def score_query_dsls(data):
        def score_query_dsl(idx):
            data.sorted_posteriors[idx], data.log_ml_estimates[idx] = english_query_to_iql_posterior(
                data.english_query, data.genparse_urls[idx], data.grammars[idx], data.pre_prompts[idx]
            )
            map_particle = data.sorted_posteriors[idx][0]["query"]
            data.queries[idx] = map_particle

        with ThreadPoolExecutor() as executor:
            executor.map(score_query_dsl, indices)
        assert all(data.queries), "Failure in scoring queries"

    def select_best_dsl(data):
        options = [idx for idx in indices if data.queries[idx]!="I can't answer that"]
        if not options:
            return -1
        return max(options, key=lambda idx: data.log_ml_estimates[idx])

    score_query_dsls(data)
    idx = select_best_dsl(data)
    data.current_dsl = DSLs[idx]
    if data.current_dsl == "OOD":
        return [{"query": OOD_REPLY, "pval": 0.999999}]
    data.parser = data.parsers[idx]
    data.interpreter = data.interpreters[idx]
    return data.sorted_posteriors[idx]


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
