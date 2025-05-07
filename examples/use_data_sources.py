import logging
import json
import requests

# !/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2025 University of Dundee & Open Microscopy Environment.
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

"""
Call the search engine to determine the available data sources"""

data_source_url = "{base_url}resources/data_sources/".format(base_url=base_url)

logging.info(" getting the available data sources")
resp = requests.get(url=data_source_url)
data_sources = json.loads(resp.text)
logging.info(
    "There are %s data sources available, i.e. %s "
    % (len(data_sources), ", ".join(data_sources))
)
"""
"The data source can be linked to queries to return search results
 from the specified data source.
For example, the user can limit the search results to "bia" data source
 when querying the searchengine for "Organism" and "homo sapiens"
 """

key = "Organism"
value = "homo sapiens"
data_source = "bia"
search_url = (
    "{base_url}resources/image/search/?key={key}&value="
    "{value}&data_source={data_source}"
).format(base_url=base_url, key=key, value=value, data_source=data_source)

resp = requests.get(url=search_url)
results = json.loads(resp.text)

logging.info(
    "The size of the returned results is %s" % results.get("results").get("size")
)
