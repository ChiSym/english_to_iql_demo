from english_to_iql_demo.pre_prompt import pre_prompt
import openai

def query_to_iql(prompt: str) -> str:
    completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}])
    return completion.choices[0].message.content

def make_prompt(user_query: str, pre_prompt:str) -> str:
    return pre_prompt.format(user_query=user_query)