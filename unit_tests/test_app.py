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
import json

from omero_search_engine.api.v1.resources.utils import (
    elasticsearch_query_builder,
    search_resource_annotation,
)

from omero_search_engine.cache_functions.elasticsearch.transform_data import (
    delete_es_index,
    # create_index
)
from test_data import (
    sql,
    valid_and_filters,
    valid_or_filters,
    not_valid_and_filters,
    not_valid_or_filters,
    query,
)

from omero_search_engine import search_omero_app, create_app

create_app("testing")


class BasicTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_api_v1(self):
        """test url"""
        tester = search_omero_app.test_client(self)

        response = tester.get("/api/v1/resources/", content_type="html/text")
        self.assertEqual(response.status_code, 200)

    def test_searchannotation(self):
        """test url"""
        tester = search_omero_app.test_client(self)
        query = {"query_details": {}}

        response = tester.post(
            "/api/v1/resources/image/searchannotation/", data=query
        )  # noqa
        self.assertEqual(response.status_code, 200)
        Error = response.json["Error"]
        self.assertIsInstance(Error, str)

    def test_not_found(self):
        """
        test not found url
        """
        tester = search_omero_app.test_client(self)
        response = tester.get("a", content_type="html/text")
        self.assertEqual(response.status_code, 404)

    def test_query_database(self):
        """
        test connection with postgresql database
        """
        res = search_omero_app.config["database_connector"].execute_query(sql)
        self.assertIsNotNone(res)
        self.assertEqual(res[0]["current_database"], "omero")

    def validate_json_syntax(self, json_template):
        try:
            return json.loads(json_template)
        except ValueError:
            print("DEBUG: JSON data contains an error")
            return False

    def validate_json_syntax_for_es_templates(self):
        pass
        # self.assertTrue(self.validate_json_syntax(image_template))
        # self.assertTrue( self.validate_json_syntax(image_template))

    def test_is_valid_json_for_query(self):
        """
        test output of query builderis valid json
        """
        query = elasticsearch_query_builder(valid_and_filters, valid_or_filters, False)
        self.assertTrue(self.validate_json_syntax(query))

    def test_is_not_valid_json_query(self):
        """
        test output of query builderis valid json
        """
        no_valid_message = elasticsearch_query_builder(
            not_valid_and_filters, not_valid_or_filters, False
        )
        self.assertTrue("Error" in no_valid_message.keys())

    def est_add_submit_query_delete_es_index(self):
        """'
        test submit query and get results
        """
        table = "image1"
        es_index = "image_keyvalue_pair_metadata_1"
        # self.assertTrue(create_index(es_index, image_template))
        res = search_resource_annotation(table, query)
        assert len(res.get("results")) >= 0
        self.assertTrue(delete_es_index(es_index))

    # def test_add_delete_es_index(self):
    #    '''
    #    test create index in elastic search
    #    :return:
    #    '''
    #    from datetime import datetime
    #    es_index_name="test_image_%s"%str(datetime.now().second)

    #   self.assertTrue (create_index(es_index_name, image_template))
    #   self.assertTrue (delete_es_index(es_index_name))

    def test_log_in_log_out(self):
        """
        test login and log out functions
        :return:
        """
        pass


if __name__ == "__main__":
    unittest.main()
