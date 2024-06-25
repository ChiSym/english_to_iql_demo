# english_to_iql_demo

### Prequisites

#### Huggingface

1. Make a [Huggingface](https://huggingface.co/) account if you don't have one.
2. Create a [huggingface user access token](https://huggingface.co/settings/tokens) if you don't have one.
3. Agree to the [gemma model conditions](https://huggingface.co/google/gemma-7b).

### Installation

1. Install [poetry](https://python-poetry.org/docs/#installation)
2. Run `poetry install`
3. Run `poetry shell`
4. Run `npm install`
4. Run `huggingface-cli login`, and paste in your user access token

### Development

1. To start the web server, run `uvicorn english_to_iql_demo.main:app --reload`
2. To work on the Tailwind CSS, run `npx tailwindcss -i ./src/input.css -o ./dist/output.css --watch`