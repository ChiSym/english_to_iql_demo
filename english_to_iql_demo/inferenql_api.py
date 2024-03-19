import requests


def make_iql_request(query: str):
    # url = "http://localhost:8080/api/query"
    # stackoverflow
    url = "http://44.200.189.145:60082/api/query"
    request_json = {"query": query}

    # make a post request

    request = requests.post(url, json = request_json)
    import ipdb; ipdb.set_trace()

if __name__ == "__main__":
    make_iql_request("SELECT * FROM developer_records")