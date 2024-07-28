# english_to_iql_demo

clone repo, checkout to ces_dispatch
poetry install (might be missing a few packages---in particular I think we were having issues with autoinstalling genjax?)
follow the genjax install instructions on the genjax repo
tar -xzvf interpreter_metadata.tar.gz
run uvicorn english_to_iql_demo.main:app --reload