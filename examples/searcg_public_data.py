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

import sys
from utils import query_the_search_ending, logging

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

"""
Find images of cells treated with a specific drug
Cell Type = "induced pluripotent stem cell" and compound = "fibronectin"
The "and" query clauses should be as follows:
"""

received_results_data = []
and_filters = [
    {
        "name": "Cell LINE",
        "value": "hela",
        "operator": "equals",
        "resource": "image",
    }
]

received_results_data = []
"""
If we need to get the results from a public data pr a private data
we can use the main attribute that can be used to add
is_public = 0 for private data
is_public = 1 for public data
"""
main_attributes = {
    "and_main_attributes": [{"name": "is_public", "value": 0, "operator": "equals"}]
}

query = {"and_filters": and_filters}

results = query_the_search_ending(query, main_attributes)
