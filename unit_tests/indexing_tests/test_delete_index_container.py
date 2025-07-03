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

"""
Basic app unit tests
"""

import unittest


from omero_search_engine.api.v1.resources.resource_analyser import (
    return_containers_images,
)

from omero_search_engine.cache_functions.elasticsearch.elasticsearch_templates import (  # noqa
    image_template,
    key_values_resource_cache_template,
)


from test_data import (
    containers_n,
    container_m,
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

        ids_ = list(containers_n.keys())
        data_source = containers_n[ids_[0]]["data_source"]
        resource = containers_n[ids_[0]]["type"]
        from omero_search_engine.api.v1.resources.utils import delete_container

        print("ids are %s" % ",".join(ids_))
        delete_container(",".join(ids_), resource, data_source, True, True)

        containers_ad = return_containers_images(
            data_source,
        )
        # test delete container
        for id, container in containers_n.items():
            for con1 in containers_ad["results"]["results"]:
                self.assertNotEquals(int(con1["id"]), int(id))
        from omero_search_engine.cache_functions.elasticsearch.transform_data import (
            index_container_from_database_,
        )

        index_container_from_database_(
            resource,
            data_source,
            ",".join(ids_),
            False,
            True,
        )

        containers_ad = return_containers_images(data_source)
        found = False
        for id, container in containers_n.items():
            for con1 in containers_ad["results"]["results"]:
                if int(con1["id"]) == int(id) and con1["type"] == container["type"]:
                    found = True
                    cur_res = con1
                    break
        self.assertTrue(found)
        self.assertEqual(int(cur_res["image count"]), int(container["image count"]))
        self.assertEqual(cur_res["name"], container["name"])

    def test_delete_index_other_container(self):
        from omero_search_engine.cache_functions.elasticsearch.transform_data import (
            index_container_from_database_,
        )
        from omero_search_engine.api.v1.resources.utils import delete_container

        ids_ = list(container_m.keys())
        data_source = container_m[ids_[0]]["data_source"]
        resource = container_m[ids_[0]]["type"]
        delete_container(",".join(ids_), resource, data_source, True, True)
        containers_ad = return_containers_images(
            data_source,
        )
        # test delete container
        for id, container in containers_n.items():
            for con1 in containers_ad["results"]["results"]:
                self.assertNotEqual(int(con1["id"]), int(id))

        index_container_from_database_(
            resource,
            data_source,
            ",".join(ids_),
            False,
            True,
        )

        # for id in containers_n:
        #    #index_container_from_database(resource, data_source,
        #    ",".join(ids_), "False", "True")
        #    index_container_from_database(resource, data_source, id, "False", "True")
        containers_ad = return_containers_images(data_source)
        found = False
        for id, container in container_m.items():
            for con1 in containers_ad["results"]["results"]:
                if int(con1["id"]) == int(id) and con1["type"] == container["type"]:
                    found = True
                    cur_res = con1
                    break
        self.assertTrue(found)
        self.assertEqual(int(cur_res["image count"]), int(container["image count"]))
        self.assertEqual(cur_res["name"], container["name"])


if __name__ == "__main__":
    unittest.main()
