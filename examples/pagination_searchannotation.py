#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2022 University of Dundee & Open Microscopy Environment.
# All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
import logging
import requests
import sys

# url to send the query
image_ext = "/resources/image/searchannotation/"
# url to get the next page for a query, bookmark is needed
image_page_ext = "/resources/image/searchannotation_page/"
# search engine url
base_url = "http://127.0.0.1:5577/api/v1/"

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

def get_bookmark(pagination_dict):
    next_page=pagination_dict["next_page"]
    for page_rcd in pagination_dict["page_records"]:
        if page_rcd["page"]==next_page:
            return page_rcd["bookmark"]

def find_all_the_results(query, main_attributes):
    received_results_data = []
    query_data = {"query": {"query_details": query, "main_attributes": main_attributes}}
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
    # get the total number of pages
    total_pages = returned_results["results"]["total_pages"]
    pagination_dict = returned_results["results"].get("pagination")

    page = pagination_dict["current_page"]

    logging.info(
        "page: %s, received results: %s"
        % (
             (str(page) + "/" + str(total_pages)),
            (str(received_results) + "/" + str(total_results)),
        )
    )
    #it is not used in the request, it is used to comapre requests using
    #pagination and bookmark
    bookmark = get_bookmark(pagination_dict)
    page=pagination_dict["next_page"]
    ids=[]
    while page:
        query_data = {
            "query": {"query_details": returned_results["query_details"]},
            "pagination": pagination_dict
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

        #bookmark = returned_results["results"].get("bookmark")
        pagination_dict = returned_results["results"].get("pagination")

        received_results = received_results + len(
            returned_results["results"]["results"]
        )
        for res in returned_results["results"]["results"]:
            if res['id'] in ids:
                raise Exception ("Image id %s is added before."%res["id"])
            ids.append(res["id"])
            received_results_data.append(res)

        logging.info(
            "bookmark: %s, page: %s, received results: %s"
            % (
                bookmark,
                (str(page) + "/" + str(total_pages)),
                (str(received_results) + "/" + str(total_results)),
            )
        )
        page = pagination_dict.get("next_page")
        bookmark=get_bookmark(pagination_dict)

    logging.info("Total received results: %s" % len(received_results_data))
    return received_results_data



# Find images of cells where a specific gene was targeted
# Cell line = "HeLa" and Gene Symbol = "KIF11"

# and filters
and_filters = [
    {"name": "Cell Line", "value": "HeLa", "operator": "equals"},
    {"name": "Gene Symbol", "value": "KIF11", "operator": "equals"},
]
main_attributes = []
query = {"and_filters": and_filters}

received_results_data = find_all_the_results(query, main_attributes)

# Another example: Cell line = "U2OS" and Gene Symbol = "RHEB"

and_filters_2 = [
    {"name": "Cell Line", "value": "U2OS", "operator": "not_equals"},
    {"name": "Gene Symbol", "value": "RHEB", "operator": "equals"},
]
query_2 = {"and_filters": and_filters_2, "case_sensitive": True}
received_results_data_2 = find_all_the_results(query_2, main_attributes)
