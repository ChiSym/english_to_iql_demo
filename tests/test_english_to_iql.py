from english_to_iql_demo.english_to_iql import make_prompt
from english_to_iql_demo.pre_prompt import pre_prompt


def test_make_prompt():
    english_query = "Show me 5 rows from the data"
    prompt = make_prompt(english_query, pre_prompt)

    assert isinstance(prompt, str)
    assert len(prompt) > len(english_query)