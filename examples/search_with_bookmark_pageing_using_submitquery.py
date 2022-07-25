import datetime
import logging
import json
import requests
import sys

# url to send the query
image_ext = "/resources/image/searchannotation/"
# url to get the next page for a query, bookmark is needed
image_page_ext = "/resources/image/searchannotation_page/"
# search engine url
base_url = "http://127.0.0.1:5577/api/v1/"
submit_query_url = "http://127.0.0.1:5577/api/v1/resources/submitquery"  # noqa


logging.basicConfig(stream=sys.stdout, level=logging.INFO)

received_results = []
page = 1
ids = []
total_pages = 0


def call_omero_searchengine_return_results(url, data=None, method="post"):
    if method == "post":
        resp = requests.post(url, data=data)
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
        # get the boomark which will be used to call
        # the next page of the results
        bookmark = returned_results["results"]["bookmark"]
        # get the size of the total results
        total_results = returned_results["results"]["size"]
        for res in returned_results["results"]["results"]:
            received_results.append(res)
            if res["id"] in ids:
                raise Exception(" Id dublicated error  %s" % res["id"])
            ids.append(res["id"])
        global total_pages
        total_pages = returned_results["results"]["total_pages"]
        return bookmark, total_results

    except Exception as ex:
        print(resp.text)
        logging.info("Error: %s" % ex)


"""
If the user needs to search for unhealthy human female breast images

Clause for Human:  
Organism='Homo sapiens' ==> {"name": "Organism", "value": "Homo sapiens", "operator": "equals","resource": "image"}  # noqa
Restrict the search to "female":
Sex='Female' ==> {"name": "Sex", "value": "Female", "operator": "equals","resource": "image"}  # noqa
Restrict the search to "breast":
Organism Part='Breast' ==>{"name": "Organism Part", "value": "Breast", "operator": "equals","resource": "image"}  # noqa
Return only the images of "abnormal" tissues: 
Pathology != 'Normal tissue, NOS' ==> {"name": "Pathology", "value": "Normal tissue, NOS", "operator": "not_equals","resource": "image"}  # noqa
In terms of clauses we only have and_filters which contains 4 clauses
"""
start = datetime.datetime.now()
and_filters = [
    {
        "name": "Organism",
        "value": "Homo sapiens",
        "operator": "equals",
        "resource": "image",
    },
    {
        "name": "Organism Part",
        "value": "Breast",
        "operator": "equals",
        "resource": "image",
    },
    {
        "name": "Sex",
        "value": "Female",
        "operator": "equals",
        "resource": "image"
    },
    {
        "name": "Pathology",
        "value": "Normal tissue, NOS",
        "operator": "not_equals",
        "resource": "image",
    },
]

query_data = {"query_details": {"and_filters": and_filters}}

query_data_json = json.dumps(query_data)
bookmark, total_results = call_omero_searchengine_return_results(
    submit_query_url, data=query_data_json
)

while len(received_results) < total_results:

    page += 1
    query_data_ = {"query_details": {"and_filters": and_filters},
                   "bookmark": bookmark}
    query_data_json_ = json.dumps(query_data_)

    bookmark, total_results = call_omero_searchengine_return_results(
        submit_query_url, data=query_data_json_
    )

    logging.info(
        "bookmark: %s, page: %s, / %s received results: %s / %s"
        % (bookmark, page, total_pages, len(received_results), total_results)
    )
