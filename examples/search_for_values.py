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
image_value_search = "/resources/image/searchvalues/"
# searchengine url
base_url = "http://127.0.0.1:5577/api/v1/"
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

"""
If the user needs to search for a value whose attribute is not known e.g.
search to find if diabetes is a part of any attribute values:
"""
search_url = "%S/%s%value=diabetes"
search_url = "{base_url}{image_value_search}?value={value}".format(
    base_url=base_url, image_value_search=image_value_search, value="diabetes"
)
resp = requests.get(url=search_url)
res = json.loads(resp.text)
# total items
logging.info("total_items: %s" % res.get("total_items"))
logging.info("total_number: %s" % res.get("total_number"))
# total number of buckets
logging.info("Number of buckets: %s" % res.get("total_number_of_buckets"))
# data
data = res.get("data")
logging.info("Number of buckets: %s" % len(data))
total_number_of_images = 0
for data_ in data:
    total_number_of_images += data_.get("Number of images")

logging.info("Total number of images: %s" % total_number_of_images)
