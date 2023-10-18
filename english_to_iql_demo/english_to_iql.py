from english_to_iql_demo.pre_prompt import pre_prompt
import polars as pl
import openai
import subprocess
import re


def prompt_to_iql(prompt: str) -> str:
    completion = openai.ChatCompletion.create(
        model="gpt-4", messages=[{"role": "user", "content": prompt}]
    )
    return "SELECT " + completion.choices[0].message.content


def english_query_to_iql(user_query: str) -> str:
    prompt = make_prompt(user_query, pre_prompt)
    return prompt_to_iql(prompt)


def make_prompt(user_query: str, pre_prompt: str) -> str:
    return pre_prompt.format(user_query=user_query)


def preprocess_iql_query(iql_query: str) -> str:
    return re.sub("\s+", " ", iql_query)