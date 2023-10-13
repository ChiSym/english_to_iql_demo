from english_to_iql_demo.english_to_iql import run_query


def test_run_query():
    english_query = "Show me 5 rows from the data"
    run_query(english_query)