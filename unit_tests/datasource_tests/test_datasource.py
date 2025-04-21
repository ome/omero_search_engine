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

"""
Basic app unit tests
"""

import unittest


from omero_search_engine.api.v1.resources.resource_analyser import (
    return_containes_images,
)

from omero_search_engine.cache_functions.elasticsearch.elasticsearch_templates import (  # noqa
    image_template,
    key_values_resource_cache_template,
)


from omero_search_engine import create_app

create_app("testing")
# deep_check should be a configuration item
deep_check = True

# for data_source in search_omero_app.config.database_connectors.keys():


class BasicTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_delete_index_one_container(self):
        from manage import (
            delete_data_source_data,
        )

        data_source = "omero_train"
        delete_data_source_data(data_source)
        from omero_search_engine.api.v1.resources.utils import get_data_sources
        import time

        time.sleep(10)
        # create_app("testing")
        print("==========================")
        data_sources = get_data_sources()
        print(data_sources)
        print("==========================")
        assert data_source not in data_sources


if __name__ == "__main__":
    unittest.main()
