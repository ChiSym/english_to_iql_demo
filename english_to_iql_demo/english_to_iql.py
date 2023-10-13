from english_to_iql_demo.pre_prompt import pre_prompt
import openai
import subprocess

def query_to_iql(prompt: str) -> str:
    completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}])
    return "SELECT " + completion.choices[0].message.content

def make_prompt(user_query: str, pre_prompt:str) -> str:
    return pre_prompt.format(user_query=user_query)

def run_query(user_query: str):
    prompt  = make_prompt(user_query, pre_prompt)
    iql = query_to_iql(prompt)
    subprocess.run(['sudo ./bin/run_iql_query_clj.sh', iql], stdout=subprocess.PIPE, stderr=subprocess.PIPE)