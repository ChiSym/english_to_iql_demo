import requests
import json
from english_to_iql_demo.pre_prompt import pre_prompt
from openai import OpenAI

def english_query_to_iql(user_query: str, genparse_url: str, grammar: str) -> str:
    prompt = pre_prompt.format(user_query=user_query)
    client = OpenAI()

    completion = client.chat.completions.create(
    model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an assistant that writes IQL, an SQL-like language for querying data. YOU WRITE ONLY IQL, NOTHING ELSE."},
            {"role": "user", "content": prompt}
        ]
    )

    text = completion.choices[0].message.content
    return text

# def english_query_to_iql(user_query: str, genparse_url: str, grammar: str) -> str:
#     prompt = pre_prompt.format(user_query=user_query)
#     request = {
#         "prompt": prompt,
#         "method": "smc-standard",
#         "n_particles": 10,
#         "lark_grammar": grammar,
#         "proposal_name": "character",
#         "proposal_args": {},
#         "max_tokens": 100,
#         "'76'": ''
#         }
#     headers ={
#         "Content-type": "application/json",
#         "Accept": "application/json"
#         }
#     x = requests.post(genparse_url, json = request, headers=headers)
#     import ipdb; ipdb.set_trace()

#     response = json.loads(x.text)
#     posterior = response['posterior']
#     map_particle = max(posterior, key=posterior.get)
#     return map_particle