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
from utils import base_url

# url to send the query
image_search = "/resources/image/search/"

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
logging.info("Searching for: Organism Homo sapiens")


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
        logging.info(
            "%s: %s contains %s images"
            % (item.get("type"), item.get("name"), item.get("image count"))
        )
