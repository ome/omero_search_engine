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

from utils import query_the_search_ending

# Find images of cells where a specific gene was targeted
# Cell line = "HeLa" and Gene Symbol = "KIF11"

# and filters
and_filters = [
    {"name": "Cell Line", "value": "HeLa", "operator": "equals"},
    {"name": "Gene Symbol", "value": "KIF11", "operator": "equals"},
]
main_attributes = []
query = {"and_filters": and_filters}

received_results_data = query_the_search_ending(query, main_attributes)

# Another example: Cell line = "U2OS" and Gene Symbol = "RHEB"

and_filters_2 = [
    {"name": "Cell Line", "value": "U2OS", "operator": "not_equals"},
    {"name": "Gene Symbol", "value": "RHEB", "operator": "equals"},
]
query_2 = {"and_filters": and_filters_2, "case_sensitive": True}
received_results_data_2 = query_the_search_ending(query_2, main_attributes)
