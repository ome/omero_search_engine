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
"""
If SearchEngine is not installed locally or if the user prefers
 to run the example using IDR, they can proceed with:
base_url = "http://idr.openmicroscopy.org/searchengine2/api/v1/"
"""

logging.basicConfig(stream=sys.stdout, level=logging.INFO)


def query_the_search_ending(query, main_attributes):
    received_results_data = []
    query_data = {"query": {"query_details": query, "main_attributes": main_attributes}}
    query_data_json = json.dumps(query_data)
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
