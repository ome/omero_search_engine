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

import logging
import json
import requests
import sys
import datetime
from utils import base_url

# url to send the query
image_ext = "/resources/image/searchannotation/"
# url to get the next page for a query, bookmark is needed
image_page_ext = "/resources/image/searchannotation_page/"

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
received_results = []
page = 1
ids = []
total_pages = 0


def call_omero_return_results(url, data=None, method="post"):
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
        # get the bookmark which will be used to call
        # the next page of the results
        bookmark = returned_results["results"]["bookmark"]
        # get the size of the total results
        total_results = returned_results["results"]["size"]
        for res in returned_results["results"]["results"]:
            received_results.append(res)
            if res["id"] in ids:
                raise Exception("Dublicated ids %s" % res["id"])
            ids.append(res["id"])
        global total_pages
        total_pages = returned_results["results"]["total_pages"]
        return bookmark, total_results

    except Exception as ex:
        logging.info("Error: %s" % ex)
        sys.exit()


"""

If the user needs to search for unhealthy human female breast tissue images:

Clause for Human:
Organism='Homo sapiens' ==> {"name": "Organism", "value": "Homo sapiens", "operator": "equals","resource": "image"}  # noqa
Restrict the search to "female":
Sex='Female' ==> {"name": "Sex", "value": "Female", "operator": "equals","resource": "image"} # noqa
Restrict the search to "breast":
Organism Part='Breast' ==>{"name": "Organism Part", "value": "Breast", "operator": "equals","resource": "image"} # noqa
Return only the images of "abnormal" tissues:
Pathology != 'Normal tissue, NOS' ==> {"name": "Pathology", "value": "Normal tissue, NOS", "operator": "not_equals","resource": "image"} # noqa
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
    {"name": "Sex", "value": "Female", "operator": "equals", "resource": "image"},
    {
        "name": "Pathology",
        "value": "Normal tissue, NOS",
        "operator": "not_equals",
        "resource": "image",
    },
]

query_data = {"query_details": {"and_filters": and_filters}}

query_data_json = json.dumps(query_data)
# resp = requests.post(url="%s%s" % (base_url, image_ext),
#                      data=query_data_json)
bookmark, total_results = call_omero_return_results(
    "%s%s" % (base_url, image_ext), data=query_data_json
)

while len(received_results) < total_results:
    page += 1
    # add bookmark to the query, so it will return the next page
    query_data_ = {
        "query": {"query_details": {"and_filters": and_filters}},
        "bookmark": bookmark,
    }
    query_data_json_ = json.dumps(query_data_)
    # call the server
    bookmark, total_results = call_omero_return_results(
        "%s%s" % (base_url, image_page_ext), data=query_data_json_
    )

    logging.info(
        "bookmark: %s, page: %s, / %s received results: %s / %s"
        % (bookmark, page, total_pages, len(received_results), total_results)
    )
