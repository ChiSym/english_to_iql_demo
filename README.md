# genfact_demo

### Installation

1. Install [poetry](https://python-poetry.org/docs/#installation)
2. Run `poetry install`
3. Run `poetry shell`
4. Run `npm install`
4. Run `huggingface-cli login`, and paste in your user access token

### Development

1. To start the web server, run `uvicorn english_to_iql_demo.main:app --reload`
2. To work on the Tailwind CSS, run `npx tailwindcss -i ./src/input.css -o ./dist/output.css --watch`