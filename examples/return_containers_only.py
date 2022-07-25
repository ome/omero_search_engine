import logging
import json
import requests
import sys


# url to send the query
image_search = "/resources/image/search/"
# search engine url
base_url = "http://127.0.0.1:5577/api/v1/"
# base_url ="https://idr-testing.openmicroscopy.org/searchengineapi/api/v1/"  # noqa


logging.basicConfig(stream=sys.stdout, level=logging.INFO)
"""
It is required to search the database for:
"Organism"="Homo sapiens" 
and return the containers only, the studies which contain the results
As it is a simple search, a single clause then search can be 
used to simplify the request
http://127.0.0.1:5577/api/v1/resources/image/search/?key=cell%20line&value=hela&return_containers=true # noqa

curl -X GET "http://127.0.0.1:5577/api/v1/resources/image/search/?key=Organism&value=Homo%20sapiens&return_containers=true" # noqa
"""

page = 0
ids = []
logging.info(" Searching for: Organism Homo sapiens")


url = "%s%s?key=Organism&value=Homo sapiens&return_containers=true" % (
    base_url,
    image_search,
)
resp = requests.get(url)
returned_results = json.loads(resp.text)
if returned_results.get("results"):
    if len(returned_results.get("results").get("results")) == 0:
        logging.info("No results is found")
    for item in returned_results.get("results").get("results"):
        logging.info("Study: %s" % item.get("Name (IDR number)"))
