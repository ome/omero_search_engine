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
import math

# url to send the query
image_value_search = "/resources/image/searchvalues/"
# searchengine url
base_url = "http://127.0.0.1:5577/api/v1/"
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

"""
If the user needs to search for a value whose attribute is not known e.g.
search to find if diabetes is a part of any attribute values:
"""
value = "pr"

search_url = "{base_url}{image_value_search}?value={value}".format(
    base_url=base_url, image_value_search=image_value_search, value=value
)

# url to send the query
image_value_search = "/resources/image/searchvalues/"
# searchengine url
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

"""
If the user needs to search for a value whose attribute is not known
e.g. search to find if p is a part of any attribute values and return
all the possible matches:
"""
search_url = "{base_url}{image_value_search}?value={value}".format(
    base_url=base_url, image_value_search=image_value_search, value=value
)
resp = requests.get(url=search_url)
res = json.loads(resp.text)
# total number of buckets
# data
data = res.get("data")
buckets = []
total_number_of_images = 0
recieved_bukets = 0
buckets = buckets + data

resp = requests.get(url=search_url)
res = json.loads(resp.text)
# total number of buckets
# data
page = 1
no_pages = math.ceil(res.get("total_number_of_all_buckets") / 9999)

logging.info("Total number of images: %s" % res.get("total_number_of_image"))
logging.info(
    "Total number of returned buckets: %s" % res.get("total_number_of_buckets")
)
logging.info("Total number of all buckets: %s" % res.get("total_number_of_all_buckets"))

bookmark = res.get("bookmark")
if bookmark:
    while True:
        page += 1

        bookmark = [str(item) for item in bookmark]
        bookmark = ",".join(bookmark)
        search_url = (
            "{base_url}{image_value_search}?value={value}&bookmark={bookmark}".format(
                base_url=base_url,
                image_value_search=image_value_search,
                value=value,
                bookmark=bookmark,
            )
        )
        resp = requests.get(url=search_url)
        try:
            ss = resp.text
            res = json.loads(ss)
        except Exception as e:
            logging.info("Error %s" % str(e))
            break
        bookmark = res.get("bookmark")
        if not bookmark:
            break
        data = res.get("data")
        buckets = buckets + data
        logging.info("Page %s/%s" % (page, no_pages))
        logging.info("Total number of images: %s" % res.get("total_number_of_image"))
        logging.info("No of buckets: %s" % res.get("total_number_of_buckets"))
