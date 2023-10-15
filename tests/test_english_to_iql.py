from english_to_iql_demo.english_to_iql import make_prompt, prompt_to_iql
from english_to_iql_demo.pre_prompt import pre_prompt


def test_make_prompt():
    english_query = "Show me 5 rows from the data"
    prompt = make_prompt(english_query, pre_prompt)

    assert isinstance(prompt, str)
    assert len(prompt) > len(english_query)

def test_query_to_iql():
    english_query = "Show me 5 rows from the data"
    prompt = make_prompt(english_query, pre_prompt)

    iql = prompt_to_iql(prompt)
    assert isinstance(iql, str)