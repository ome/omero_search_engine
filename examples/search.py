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


# url to send the query
image_search = "/resources/image/search/"
# search engine url
base_url = "http://127.0.0.1:5577/api/v1/"
#base_url = "https://idr-testing.openmicroscopy.org/searchengine/api/v1/"  # noqa


logging.basicConfig(stream=sys.stdout, level=logging.INFO)
"""
It is required to search the database for:
"Organism"="Homo sapiens"
As it is a simple search, a single clause then
search can be used to simplify the request

curl -X GET "http://127.0.0.1:5577/api/v1/resources/image/search/?key=Organism&value=Homo%20sapiens"  # noqa
"""
received_results = []
page = 0
ids = []
logging.info(" Searching for:  Organism Homo sapiens")


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
        # get the boomark which will be used to call the next page of
        # the results
        bookmark = returned_results["results"]["bookmark"][0]
        # get the size of the total results
        total_results = returned_results["results"]["size"]
        total_pages = returned_results["results"]["total_pages"]
        for res in returned_results["results"]["results"]:
            received_results.append(res)
        return bookmark, total_results, total_pages

    except Exception as ex:
        logging.info("Error: %s" % str(ex))
        sys.exit()


url = "%s%s?key=Organism&value=Homo sapiens" % (base_url, image_search)
bookmark, total_results, total_pages = call_omero_return_results(
    url, method="get"
)  # noqa

while len(received_results) < total_results:
    page += 1
    url_ = url + "&bookmark=%s" % bookmark
    bookmark, total_results, total_pages = call_omero_return_results(
        url_, method="get"
    )  # noqa
    logging.info(
        "received: %s /%s, page: %s/%s, bookmark:  %s"
        % (len(received_results), total_results, page, total_pages, bookmark)
    )

# 2000 /11686633, page: 1/11687, bookmark: 109600
# 2000 /12225067, page: 1/12226, bookmark:  109600
