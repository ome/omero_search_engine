import logging
import requests
import json

# url to send the query
# search engine url
submit_query_url = "http://127.0.0.1:5577/api/v1/resources/submitquery_returnstudies/"

# base_url ="https://idr-testing.openmicroscopy.org/searchengineapi/api/v1/"
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
"""
The following query will answer this question:
Get a list of studies which satsidy the following conditions:
"Organism"="mus musculus" 
 and 
"Imaging Method"="light sheet fluorescence microscopy, spim"
"""
recieved_results = []

logging.info(
    "Get a study list for:  (Organism= mus musculus) and (Imaging Method=light sheet fluorescence microscopy, spim)"
)

"""
url="%s%s?key=Organism&value=Homo sapiens&return_containers=true"%(base_url,image_search)
resp = requests.get(url)
returned_results = json.loads(resp.text)
if returned_results.get("results"):
    if len(returned_results.get("results").get("results"))==0:
        logging.info ("No results is found")
    for item in returned_results.get("results").get("results"):
        logging.info ("Study: %s"%item.get("Name (IDR number)"))
"""

data = {
    "resource": "image",
    "query_details": {
        "and_filters": [
            {
                "name": "Organism",
                "value": "mus musculus",
                "operator": "equals",
                "resource": "image",
            },
            {
                "name": "Imaging Method",
                "value": "light sheet fluorescence microscopy, spim",
                "operator": "equals",
                "resource": "project",
            },
        ],
        "or_filters": [],
        "case_sensitive": False,
    },
}

resp = requests.post(submit_query_url, data=json.dumps(data))
returned_results = json.loads(resp.text)
if returned_results.get("results"):
    if len(returned_results.get("results").get("results")) == 0:
        logging.info("No results is found")
    for item in returned_results.get("results").get("results"):
        logging.info("Study: %s" % item.get("Name (IDR number)"))
