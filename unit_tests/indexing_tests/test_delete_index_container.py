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

from omero_search_engine.api.v1.resources.utils import (
    update_data_source_cache,
    delete_container,
)

from omero_search_engine.api.v1.resources.resource_analyser import (
    return_containes_images,
)

from omero_search_engine.cache_functions.elasticsearch.elasticsearch_templates import (  # noqa
    image_template,
    key_values_resource_cache_template,
)

from omero_search_engine.cache_functions.elasticsearch.transform_data import (
    index_container_s_from_database,
)


from test_data import (
    containers_1,
    containers_2,
)

from omero_search_engine import search_omero_app, create_app

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
        import time

        # test delete container
        for id, container in containers_1.items():
            delete_container(id, container["type"], container["data_source"], False)
            update_data_source_cache(container["data_source"])
            time.sleep(60)
            containers_ad = return_containes_images(
                container["data_source"],
            )
            for con1 in containers_ad["results"]["results"]:
                self.assertNotEquals(int(con1["id"]), int(id))

        # test index container
        resources_index = {
            "project": ["image", "project"],
            "screen": ["image", "screen", "well", "plate"],
        }
        for id, container in containers_1.items():
            for res in resources_index[container["type"]]:
                index_container_s_from_database(
                    container["type"], res, id, container["data_source"]
                )

            update_data_source_cache(container["data_source"])
            search_omero_app.logger.info("Waiting to index the data... ")

            time.sleep(60)
            # return_containes_images
            containers_ai = return_containes_images(container["data_source"])

            found = False
            cur_res = None
            for con1 in containers_ai["results"]["results"]:
                if int(con1["id"]) == int(id) and con1["type"] == container["type"]:
                    found = True
                    cur_res = con1
                    break
            self.assertTrue(found)
            self.assertEqual(int(cur_res["image count"]), int(container["image count"]))
            self.assertEqual(cur_res["name"], container["name"])

        # def test_delete_index_multi_containers(self):
        resources_index = {
            "project": ["image", "project"],
            "screen": ["image", "screen", "well", "plate"],
        }
        import time

        ids = []
        data_source = ""
        resource = ""
        for id in containers_2:
            data_source = containers_2[id]["data_source"]
            resource = containers_2[id]["type"]
            ids.append(id)
        delete_container(",".join(ids), resource, data_source, True)
        time.sleep(60)
        # return_containes_images
        containers_ad = return_containes_images(data_source)

        for id, container in containers_2.items():
            for con1 in containers_ad["results"]["results"]:
                self.assertNotEquals(int(con1["id"]), int(id))

        for res in resources_index[resource]:
            index_container_s_from_database(resource, res, ",".join(ids), data_source)
        update_data_source_cache(data_source)
        time.sleep(60)
        containers_ai = return_containes_images(data_source)
        found = False
        cur_res = None
        for id, container in containers_2.items():
            for con1 in containers_ai["results"]["results"]:
                if int(con1["id"]) == int(id) and con1["type"] == container["type"]:
                    found = True
                    cur_res = con1
                    break
        self.assertTrue(found)
        self.assertEqual(int(cur_res["image count"]), int(container["image count"]))
        self.assertEqual(cur_res["name"], container["name"])


if __name__ == "__main__":
    unittest.main()
