# english_to_iql_demo

### Installation

1. Install [poetry](https://python-poetry.org/docs/#installation)
2. Follow the GenJax prerequisite instructions [here](https://github.com/probcomp/genjax/?tab=readme-ov-file#quickstart)
3. `poetry install` - (may have issues with genjax - try asking Sam for help - pip install may work)
4. `poetry shell`
5. `npm install`
6. `tar -xzvf interpreter_metadata.tar.gz`
7. `tar -xzvf geodataframe.tar.gz`
8. You may also need to download and install some extra files that are over the Github acceptable size limit (e.g., synthetic_data.parquet)


### Development

To start the web server, run `uvicorn english_to_iql_demo.main:app --reload`. It will be available on localhost at port 8000.


### Production

To start the web server for production, run:
1. `poetry shell`
2. `uvicorn english_to_iql_demo.main:app --host 0.0.0.0 --port 60000 --workers 1 > uvicorn.log 2>&1 &`
3. `disown`

`--host 0.0.0.0` tells it to listen from all IP addresses. By default, it only listens to localhost (which is fine for development using SSH tunneling).

`--workers 1` - not sure if 1 is good/bad, but it's what I've been using.

`> uvicorn.log 2>&1 &` - this redirects stdout to uvicorn.log, and redirects stderr to stdout

`&` - runs it in the background. 

`disown` is used to detach the process from the terminal so it doesn't die when you log out.

