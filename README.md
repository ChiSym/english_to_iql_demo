# english_to_iql_demo

clone repo
follow the genjax install instructions on the genjax repo
poetry install (sometimes presents issues with genjax)
tar -xzvf interpreter_metadata.tar.gz
tar -xzvf geodataframe.tar.gz
run uvicorn english_to_iql_demo.main:app --reload