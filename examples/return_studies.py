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
# search engine url
submit_query_url = (
    "http://127.0.0.1:5577/api/v1/resources/submitquery_returnstudies/"  # noqa
)

# base_url ="https://idr-testing.openmicroscopy.org/searchengineapi/api/v1/"


logging.basicConfig(stream=sys.stdout, level=logging.INFO)
"""
The following query will answer this question:
Get a list of studies which satisfy the following conditions:
"Organism"="mus musculus"
 and
"Imaging Method"="light sheet fluorescence microscopy, spim"
"""

logging.info(
    "Get a study list for:  (Organism= mus musculus) and \
    (Imaging Method=light sheet fluorescence microscopy, spim)"
)

"""
url="%s%s?key=Organism&value=Homo sapiens&return_containers=true"%(base_url,image_search)  # noqa
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
