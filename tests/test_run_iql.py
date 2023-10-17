from english_to_iql_demo.english_to_iql import run_iql_query, iql_query_to_dataframe
import polars as pl


def test_run_query():
    english_query = "Show me 5 rows from the data"
    run_iql_query(english_query)


def test_iql_query_to_dataframe():
    iql_query = "SELECT * FROM developer_records LIMIT 1000"

    df = iql_query_to_dataframe(iql_query)

    assert isinstance(df, pl.DataFrame)
    assert len(df) == 1000
