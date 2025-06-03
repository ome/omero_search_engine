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
import requests
import json
import sys
from utils import base_url

# url to send the query
image_value_search = "/resources/image/searchvalues/"
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
# Get the available attributes for a resource, e.g. image
image_attributes = "/resources/image/keys/"
# Get available values for a resource attribute
image_key_values = "resources/image/searchvaluesusingkey/"


"""
In case the user needs to know the available attributes for images
"""
attrs_url = "{base_url}{image_attributes}".format(
    image_attributes=image_attributes, base_url=base_url
)

resp = requests.get(url=attrs_url)
ress = json.loads(resp.text)
# a list containing the available attributes
for res in ress:
    data_source = res.get("data_source")
    if not data_source:
        continue
    print("Checking data source: %s " % data_source)
    attributes = res.get("image")
    logging.info(
        "Number of available attributes for images: %s" % len(attributes)
    )  # noqa

    """
    The user can get the available values for the "Organism" attribute
    and the number of images for each value
    """
    key = "Organism"
    values_attr_url = (
        "{base_url}{image_key_values}?key={key}&data_source={data_source}".format(
            base_url=base_url,
            image_key_values=image_key_values,
            key=key,
            data_source=data_source,
        )
    )
    print(values_attr_url)
    resp = requests.get(url=values_attr_url)
    res = json.loads(resp.text)
    # a list containing dicts of the available values with the number of images
    buckets = res.get("data")
    logging.info(
        "Number of available buckets for attribute %s is %s" % (key, len(buckets))
    )
    # The first bucket
    for bucket in buckets:
        logging.info("Bucket details: %s " % bucket)
