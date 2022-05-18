import requests
from datetime import datetime
import json
import logging
import sys

# url to send the query
image_ext = "/resources/image/searchannotation/"
# url to get the next page for a query, bookmark is needed
image_page_ext = "/resources/image/searchannotation_page/"
# search engine url
#base_url = "http://idr-testing.openmicroscopy.org/searchengineapi/api/v1/"
base_url = "http://127.0.0.1:5577/api/v1/"



logging.basicConfig(stream=sys.stdout, level=logging.INFO)

def query_the_search_ending(query, main_attributes):
    recieved_results_data=[]
    query_data = {"query": {'query_details': query,"main_attributes":main_attributes}}
    query_data_json = json.dumps(query_data)
    #resp = requests.post(url="%s%s" % (base_url, image_ext), data=query_data_json)
    resp = requests.post(url="%s%s" % (base_url, image_ext), data=json.dumps(query_data))

    res = resp.text
    try:
        returned_results = json.loads(res)
    except:
        logging.info(res)
        return []

    if not returned_results.get("results") or len(returned_results["results"]) == 0:
        logging.info("Your query returns no results")
        return []


    logging.info("Query results:")
    total_results = returned_results["results"]["size"]
    logging.info("Total no of result records %s" % total_results)
    logging.info("Server query time: %s seconds" % returned_results["server_query_time"])
    logging.info("Included results in the current page %s" % len(returned_results["results"]["results"]))


    for res in returned_results["results"]["results"]:
        recieved_results_data.append(res)

    recieved_results = len(returned_results["results"]["results"])
    #et the bookmar to used in the next the page, if the number of pages is bigger than 1
    bookmark = returned_results["results"]["bookmark"]
    #get the total number of pages
    total_pages = returned_results["results"]["total_pages"]
    page = 1
    logging.info("bookmark: %s, page: %s, received results: %s" % (
    bookmark, (str(page) + "/" + str(total_pages)), (str(recieved_results) + "/" + str(total_results))))
    while recieved_results < total_results:
        page += 1
        query_data = {"query": {'query_details': returned_results["query_details"]}, "bookmark": bookmark}
        query_data_json = json.dumps(query_data)
        resp = requests.post(url="%s%s" % (base_url, image_page_ext), data=query_data_json)
        res = resp.text
        try:
            returned_results = json.loads(res)
        except Exception as e:
            logging.info("%s, Error: %s"%(resp.text,e))
            return
        bookmark = returned_results["results"]["bookmark"]
        recieved_results = recieved_results + len(returned_results["results"]["results"])
        for res in returned_results["results"]["results"]:
            recieved_results_data.append(res)

        logging.info("bookmark: %s, page: %s, received results: %s" % (
        bookmark, (str(page) + "/" + str(total_pages)), (str(recieved_results) + "/" + str(total_results))))


    logging.info("Total received results: %s" % len(recieved_results_data))
    return recieved_results_data
