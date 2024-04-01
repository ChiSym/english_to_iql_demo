from english_to_iql_demo.pre_prompt import pre_prompt
import re


def prompt_to_iql(model, tokenizer, prompt: str) -> str:
    input_ids = tokenizer(prompt, return_tensors="pt").to("cuda")

    outputs = model.generate(**input_ids, max_new_tokens=200)
    return "SELECT " + tokenizer.decode(outputs[0])

def english_query_to_iql(model, tokenizer, user_query: str) -> str:
    prompt = make_prompt(user_query, pre_prompt)
    output = prompt_to_iql(model, tokenizer, prompt)

    filtered_output = output.replace(prompt, "")
    filtered_output = filtered_output.replace("<eos>", "")
    filtered_output = filtered_output.replace("<bos>", "")
    response = filtered_output.split("\n\n")[0]

    return response


def make_prompt(user_query: str, pre_prompt: str) -> str:
    return pre_prompt.format(user_query=user_query)


def preprocess_iql_query(iql_query: str) -> str:
    return re.sub("\s+", " ", iql_query)