import requests
import json

jwt_token = "<token>"
auth_url = "http://127.0.0.1:5577/auth/login"
check_toke = "http://127.0.0.1:5577/auth/verify_token/"
# username and password for the data source
data = {"username": "user-49", "password": "omero", "data_source": "omero"}
# call searchengine to authenticate and authorize the user and get the token
response = requests.post(auth_url, json=data)
# extract the token from the response
jwt_token = json.loads(response.text)

print(jwt_token)
# create the Authorization to be sent with each request
# to allow the user to search the data
head = {
    "Authorization": f"Bearer {jwt_token.get("token")}",
    "Content-Type": "application/json",
}
response = requests.get(check_toke, headers=head)
print(response.text)
# search url
query_url = "http://127.0.0.1:5577/api/v1/resources/image/searchannotation/"
# query the images for "cell line=hela"
query = {
    "query_details": {
        "and_filters": [{"name": "cell line", "value": "hela", "operator": "equals"}],
        "or_filters": [],
        "case_sensitive": False,
    }
}


def get_results(resp):
    """
    extract the results from the response
    """
    res = resp.text
    try:
        returned_results = json.loads(res)
        total_results = returned_results["results"]["size"]
        print("Total image:", total_results)
        """
        Please refer to this example
            pagination_searchannotation.py
        to extract the full results and use pagination to get the full results
        """

    except Exception as e:
        print("Error %s" % e)
        print(res)


# call without token will return error message
resp = requests.post(query_url, data=json.dumps(query))
get_results(resp)
# call with the token, it will return the user results
resp = requests.post(query_url, data=json.dumps(query), headers=head)
get_results(resp)
