#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2026 University of Dundee & Open Microscopy Environment.
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

from omero_search_engine.cache_functions.elasticsearch.elasticsearch_templates import (  # noqa
    image_template,
    key_values_resource_cache_template,
)

from omero_search_engine.validation.results_validator import (
    Validator,
    # test_csv_data_sources,
    # check_number_images_sql_containers_using_ids,
)
from omero_search_engine.cache_functions.elasticsearch.transform_data import (
    delete_es_index,
    create_index,
    get_all_indexes_from_elasticsearch,
)

from unit_tests.test_data import (
    sql,
    valid_and_filters,
    valid_or_filters,
    not_valid_and_filters,
    not_valid_or_filters,
    query,
    query_image_and,
    query_image_or,
    query_image_and_or,
    simple_queries,
    query_in,
    contains_not_contains_queries,
    image_owner,
    image_group,
    data_source,
)

from omero_search_engine import search_omero_app, create_app

create_app("testing")
# deep_check should be a configuration item
deep_check = False

# for data_source in search_omero_app.config.database_connectors.keys():


class BasicTestCase(unittest.TestCase):
    def setUp(self):
        self.data_source = data_source

    def tearDown(self):
        pass

    def test_api_v1(self):
        """test url"""
        tester = search_omero_app.test_client(self)
        response = tester.get("/api/v1/resources/", content_type="html/text")
        self.assertEqual(response.status_code, 401)

    def test_searchannotation(self):
        """test url"""
        tester = search_omero_app.test_client(self)
        query = {"query_details": {}}

        response = tester.post(
            "/api/v1/resources/image/searchannotation/", data=query
        )  # noqa
        self.assertEqual(response.status_code, 401)
        res_text = response.text
        print(res_text)
        self.assertTrue("please provide JWT token" in res_text)

    def test_not_found(self):
        """
        test not found url
        """
        tester = search_omero_app.test_client(self)
        response = tester.get("a", content_type="html/text")
        self.assertEqual(response.status_code, 401)

    def test_query_database(self):
        """
        test connection with postgresql database
        """
        # data_source = "idr"
        res = search_omero_app.config.database_connectors[
            self.data_source
        ].execute_query(sql)
        self.assertIsNotNone(res)
        found_db_name = False
        for source in search_omero_app.config.get("DATA_SOURCES"):
            if (
                source.get("DATABASE").get("DATABASE_NAME")
                == res[0]["current_database"]
            ):
                found_db_name = True
                break

        self.assertTrue(found_db_name)
        # self.assertEqual(res[0]["current_database"],
        # search_omero_app.config.database_connectors[data_source]["DATABASE_NAME"])
        # self.assertEqual(res[0]["current_database"],
        # search_omero_app.config.database_connectors[data_source]["DATABASE_NAME"])

    def validate_json_syntax(self, json_template):
        try:
            return json.loads(json_template)
        except ValueError:
            print("DEBUG: JSON data contains an error")
            return False

    def validate_json_syntax_for_es_templates(self):
        self.assertTrue(self.validate_json_syntax(image_template))
        self.assertTrue(self.validate_json_syntax(image_template))

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

    def test_add_submit_query_delete_es_index(self):
        """'
        test submit query and get results
        """
        # table = "image1"
        table_2 = "image"
        es_index = "image_keyvalue_pair_metadata_1"
        es_index_2 = "key_values_resource_cached"
        create_es_index_2 = True
        all_all_indices = get_all_indexes_from_elasticsearch()
        if es_index_2 in all_all_indices:
            create_es_index_2 = False

        if es_index not in all_all_indices:
            self.assertTrue(create_index(es_index, image_template))
        if create_es_index_2:
            self.assertTrue(
                create_index(es_index_2, key_values_resource_cache_template)
            )
        res = search_resource_annotation(table_2, query)
        assert len(res.get("results")) >= 0
        self.assertTrue(delete_es_index(es_index))
        if create_es_index_2:
            self.assertTrue(delete_es_index(es_index_2))

    def test_single_query(self):
        """
        test query the search engine and compare
        its results with the results from the database
        """
        # data_source = "idr"
        for resource, cases in simple_queries.items():
            for case in cases:
                name = case[0]
                value = case[1]
                validator = Validator(self.data_source, deep_check)
                validator.set_simple_query(resource, name, value)
                try:
                    validator.get_results_searchengine("equals")
                except Exception as e:
                    self.assertEqual(
                        str(e),
                        "Non valid token",
                    )

    def test_and_query(self):
        name = "query_image_and"
        # data_source = "idr"
        for cases in query_image_and:
            validator = Validator(self.data_source, deep_check)
            validator.set_complex_query(name, cases)
            try:
                validator.compare_results()
            except Exception as e:
                self.assertEqual(
                    str(e),
                    "Non valid token",
                )

    def test_or_query(self):
        # data_source = "idr"
        name = "query_image_or"
        for cases in query_image_or:
            validator = Validator(self.data_source, deep_check)
            validator.set_complex_query(name, cases)
            try:
                validator.compare_results()
            except Exception as e:
                self.assertEqual(
                    str(e),
                    "Non valid token",
                )

    # def test_no_images_containers(self):
    #    for data_source in search_omero_app.config.database_connectors.keys():
    #        self.assertTrue(check_number_images_sql_containers_using_ids(data_source))

    def test_multi_or_quries(self):
        pass

    def test_complex_query(self):
        # data_source = "idr"
        name = "query_image_and_or"
        for cases in query_image_and_or:
            validator = Validator(self.data_source, deep_check)
            validator.set_complex_query(name, cases)
            try:
                validator.compare_results()
            except Exception as e:
                self.assertEqual(
                    str(e),
                    "Non valid token",
                )

    def test_in_query(self):
        # data_source = "idr"
        for resource, cases in query_in.items():
            for case in cases:
                validator = Validator(self.data_source, deep_check)
                validator.set_in_query(case, resource)
                try:
                    validator.compare_results()
                except Exception as e:
                    self.assertEqual(
                        str(e),
                        "Non valid token",
                    )

    def test_not_in_query(self):
        # data_source = "idr"
        for resource, cases in query_in.items():
            for case in cases:
                validator = Validator(self.data_source, deep_check)
                validator.set_in_query(case, resource, type="not_in_clause")
                try:
                    validator.compare_results()
                except Exception as e:
                    self.assertEqual(
                        str(e),
                        "Non valid token",
                    )

    def test_contains_not_contains_queries(self):
        # data_source = "idr"
        for resource, cases in contains_not_contains_queries.items():
            for case in cases:
                name = case[0]
                value = case[1]
                validator = Validator(self.data_source, deep_check)
                validator.set_contains_not_contains_query(resource, name, value)
                try:
                    validator.get_results_searchengine("contains")
                except Exception as e:
                    self.assertEqual(
                        str(e),
                        "Non valid token",
                    )

    def test_owner(self):
        # data_source = "idr"
        for resource, cases in image_owner.items():
            for case in cases:
                name = case[0]
                value = case[1]
                owner_id = case[2]
                validator = Validator(self.data_source, deep_check)
                validator.set_simple_query(resource, name, value)
                validator.set_owner_group(owner_id=owner_id)
                try:
                    validator.compare_results()
                except Exception as e:
                    self.assertEqual("Non valid token", str(e))

    def test_group(self):
        # data_source = "idr"
        for resource, cases in image_group.items():
            for case in cases:
                name = case[0]
                value = case[1]
                group_id = case[2]
                validator = Validator(self.data_source, deep_check)
                validator.set_simple_query(resource, name, value)
                validator.set_owner_group(group_id=group_id)
                try:
                    validator.compare_results()
                except Exception as e:
                    self.assertEqual(
                        str(e),
                        "Non valid token",
                    )

    def test_log_in_log_out(self):
        """
        test login and log out functions
        :return:
        """
        pass


if __name__ == "__main__":
    unittest.main()
