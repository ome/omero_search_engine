#!/usr/bin/env python
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

import sys
from utils import query_the_search_ending, logging

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

"""
This example will use search by value only without key
It will search for the images which have key/value
pairs which the value contains cancer"""

query = {
    "and_filters": [
        {"value": "cancer", "operator": "contains"},
    ],
    "or_filters": [],
}

main_attributes = []
logging.info("Sending the query:")
results_1 = query_the_search_ending(query, main_attributes)

and_filters = [
    {"name": "cell line", "value": "hela", "operator": "equals"},
    {"value": "kif", "operator": "contains"},
]
query = {"and_filters": and_filters, "or_filters": []}

logging.info("Sending the second query:")
results_2 = query_the_search_ending(query, main_attributes)
