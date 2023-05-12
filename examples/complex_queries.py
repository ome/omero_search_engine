import json
import logging
import requests
import sys

# url to send the query
image_ext = "/resources/image/searchannotation/"
# url to get the next page for a query, bookmark is needed
image_page_ext = "/resources/image/searchannotation_page/"
# search engine url
base_url = "http://idr-testing.openmicroscopy.org/searchengine//api/v1/"
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

"""
**Query 1**
Organism Part           Small intestine OR Duodenum
Pathology               Adenocarcinoma (all) ==> contains (adenocarcinoma)
Gene Symbol             PDX1

"""
query_1 = {
    "query_details": {
        "and_filters": [
            {
                "name": "Gene Symbol",
                "value": "PDX1",
                "operator": "equals",
                "resource": "image",
            },
            {
                "name": "Pathology",
                "value": "adenocarcinoma",
                "operator": "contains",
                "resource": "image",
            },
        ],
        "or_filters": [
            [
                {
                    "name": "Organism Part",
                    "value": "Duodenum",
                    "operator": "equals",
                    "resource": "image",
                },
                {
                    "name": "Organism Part",
                    "value": "Small intestine",
                    "operator": "equals",
                    "resource": "image",
                },
            ]
        ],
        "case_sensitive": False,
    }
}

"""
**Query 2**
Organism Part           Small intestine OR Duodenum
Pathology               normal nos ==> normal tissue, nos
Gene Symbol             PDX1
"""
query_2 = {
    "query_details": {
        "and_filters": [
            {
                "name": "Gene Symbol",
                "value": "PDX1",
                "operator": "equals",
                "resource": "image",
            },
            {
                "name": "Pathology",
                "value": "normal tissue, nos",
                "operator": "equals",
                "resource": "image",
            },
        ],
        "or_filters": [
            [
                {
                    "name": "Organism Part",
                    "value": "Duodenum",
                    "operator": "equals",
                    "resource": "image",
                },
                {
                    "name": "Organism Part",
                    "value": "Small intestine",
                    "operator": "equals",
                    "resource": "image",
                },
            ]
        ],
        "case_sensitive": False,
    }
}


def query_the_search_ending(query):
    received_results_data = []
    query_data = {"query": query}
    resp = requests.post(
        url="%s%s" % (base_url, image_ext), data=json.dumps(query_data)
    )

    res = resp.text
    try:
        returned_results = json.loads(res)
    except Exception:
        logging.info(res)
        return []

    if not returned_results.get("results") or len(returned_results["results"]) == 0:
        logging.info("Your query returns no results")
        return []

    logging.info("Query results:")
    total_results = returned_results["results"]["size"]
    logging.info("Total no of result records %s" % total_results)
    logging.info(
        "Server query time: %s seconds" % returned_results["server_query_time"]
    )
    logging.info(
        "Included results in the current page %s"
        % len(returned_results["results"]["results"])
    )

    for res in returned_results["results"]["results"]:
        received_results_data.append(res)

    received_results = len(returned_results["results"]["results"])
    # set the bookmark to used in the next the page,
    # if the number of pages is greater than 1
    bookmark = returned_results["results"]["bookmark"]
    # get the total number of pages
    total_pages = returned_results["results"]["total_pages"]
    page = 1
    logging.info(
        "page: %s, received results: %s"
        % (
            (str(page) + "/" + str(total_pages)),
            (str(received_results) + "/" + str(total_results)),
        )
    )
    while received_results < total_results:
        page += 1
        query_data = {
            "query": {"query_details": returned_results["query_details"]},
            "bookmark": bookmark,
        }
        query_data_json = json.dumps(query_data)
        resp = requests.post(
            url="%s%s" % (base_url, image_page_ext), data=query_data_json
        )
        res = resp.text
        try:
            returned_results = json.loads(res)
        except Exception as e:
            logging.info("%s, Error: %s" % (resp.text, e))
            return
        received_results = received_results + len(
            returned_results["results"]["results"]
        )
        for res in returned_results["results"]["results"]:
            received_results_data.append(res)

        logging.info(
            "bookmark: %s, page: %s, received results: %s"
            % (
                bookmark,
                (str(page) + "/" + str(total_pages)),
                (str(received_results) + "/" + str(total_results)),
            )
        )
        bookmark = returned_results["results"]["bookmark"]

    logging.info("Total received results: %s" % len(received_results_data))
    return received_results_data


logging.info("Sending the first query:")
results_1 = query_the_search_ending(query_1)
logging.info("=========================")
logging.info("Sending the second query:")
results_2 = query_the_search_ending(query_2)
