import logging
import requests
import json
# url to send the query
image_search = "/resources/image/search/"
# search engine url
base_url = "http://127.0.0.1:5577/api/v1/"
import sys
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
'''
It is required to search the database for:
"Organism"="Homo sapiens"
As it is a simple search, a single clause then search can be used to simplfy the request

curl -X GET "http://127.0.0.1:5577/api/v1/resources/image/search/?key=Organism&value=Homo%20sapiens"
'''
recieved_results=[]
page=0
ids=[]
logging.info(" Searching for:  OrganismHomo sapiens")
def call_omero_return_results(url, data=None, method="post"):
    if method == "post":
        resp = requests.psot(url, data=data)
    else:
        resp = requests.get(url)
    try:
        returned_results = json.loads(resp.text)
        if not returned_results.get("results"):
            logging.info(returned_results)
            sys.exit()

        elif len(returned_results["results"]) == 0:
            logging.info("Your query returns no results")
            sys.exit()
        # get the boomark which will be used to call the next page of the results
        bookmark = returned_results["results"]["bookmark"][0]
        # get the size of the total results
        total_results = returned_results["results"]["size"]
        total_pages=returned_results["results"]["total_pages"]
        for res in returned_results["results"]["results"]:
            recieved_results.append(res)
        return bookmark, total_results, total_pages

    except Exception as ex:
        logging.info("Error: %s" % e)
        sys.exit()

url="%s%s?key=Organism&value=Homo sapiens"%(base_url,image_search)
bookmark, total_results, total_pages=call_omero_return_results(url, method="get")

while len(recieved_results)<total_results:
    page+=1
    url_=url+"&bookmark=%s"%bookmark
    bookmark, total_results, total_pages=call_omero_return_results(url_, method="get")
    logging.info("recieved: %s /%s, page: %s/%s, bookmark:  %s"%(len(recieved_results),total_results,page,total_pages, bookmark))
