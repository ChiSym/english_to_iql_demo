from english_to_iql_demo.pre_prompt import pre_prompt
from english_to_iql_demo.inferenql_api import make_iql_request
import polars as pl
import re

def prompt_to_iql(prompt: str, model_pipeline, tokenizer) -> str:
    sequences = model_pipeline(
        prompt,
        do_sample=True,
        top_k=10,
        temperature=0.1,
        top_p=0.95,
        num_return_sequences=1,
        eos_token_id=tokenizer.eos_token_id,
        max_length=200,
    )

    import ipdb; ipdb.set_trace()
    return "SELECT " + sequences[0]['generated_tex']


def english_query_to_iql(user_query: str, model_pipeline, tokenizer) -> str:
    prompt = make_prompt(user_query, pre_prompt)
    return prompt_to_iql(prompt, model_pipeline, tokenizer)


def make_prompt(user_query: str, pre_prompt: str) -> str:
    return pre_prompt.format(user_query=user_query)


def run_english_query(user_query: str):
    prompt = make_prompt(user_query, pre_prompt)
    iql_query = english_query_to_iql(prompt)
    run_iql_query(iql_query)


def preprocess_iql_query(iql_query: str) -> str:
    return re.sub("\s+", " ", iql_query)


def run_iql_query(iql_query: str):
    iql_query = preprocess_iql_query(iql_query)
    result = make_iql_request(iql_query)
    # subprocess.run(f"sudo ./bin/run_iql_query_clj.sh '{iql_query}'", shell=True)


def iql_query_to_dataframe(iql_query: str) -> pl.DataFrame:
    run_iql_query(iql_query)
    return pl.read_csv("results/iql_out.csv")
