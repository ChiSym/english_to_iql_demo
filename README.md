# english_to_iql_demo

Instructions:

- install poetry
- run `poetry install`
- make a huggingface account, and agree to the gemma conditions https://huggingface.co/google/gemma-7b
- create a huggingface authentication token
- run `huggingface-cli login`, paste your token
- run `uvicorn english_to_iql_demo.main:app --reload`