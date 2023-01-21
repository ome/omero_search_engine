#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2023 University of Dundee & Open Microscopy Environment.
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

from utils import base_url
import requests, json
import logging

'''
Return the available  keys in a containers
Also get the aviable values for a key '''

resource="image"
container_name="idr0034"
key="cell line"

#the following url will return the existing key in this container
keys_url = "{base_url}resources/image/container_keys/?container_name={container_name}".format(
    base_url=base_url, container_name=container_name)

resp = requests.get(url=keys_url)
keys_results = json.loads(resp.text)
for result in keys_results:
    logging.info ("%s: %s"%(result.get("type"), result.get("name")))
    for bucket in result.get("results"):
        logging.info ("Key: %s, no of images: %s "%(bucket.get("key"), bucket.get("no_image")))

#It is possible to get all the available values for a key
values_key_url="{base_url}resources/image/container_keyvalues/?container_name={container_name}&key={key}".format(
    base_url=base_url, container_name=container_name, key=key)

resp = requests.get(url=values_key_url)

key_values_results = json.loads(resp.text)

for result in key_values_results:
    logging.info ("%s: %s"%(result.get("type"), result.get("name")))
    for bucket in result.get("results"):
        logging.info ("Key: %s, value: %s, no of images: %s "%(bucket.get("key"),bucket.get("value"), bucket.get("no_image")))
