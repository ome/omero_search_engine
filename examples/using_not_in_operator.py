#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2024 University of Dundee & Open Microscopy Environment.
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


from utils import query_the_search_ending, logging

# It is similar to use the 'not in' operator in a sql statement,
# rather than having multiple 'or' conditions with not_equals operators,
# it will only use a single condition.

# The following example will search for the images which have met any of the 'Organism'
# values in this list
# ["homo sapiens","mus musculus","mus musculus x mus spretus","human adenovirus 2"]

# and filters

logging.info("Example of using not_in operator")


values_not_in = [
    "homo sapiens",
    "mus musculus",
    "mus musculus x mus spretus",
    "human adenovirus 2",
]
logging.info("Searching for 'Organism' with values in [%s]" % (",".join(values_not_in)))
and_filters = [{"name": "Organism", "value": values_not_in, "operator": "not_in"}]

main_attributes = []
query = {"and_filters": and_filters}
#
recieved_results_data = query_the_search_ending(query, main_attributes)
