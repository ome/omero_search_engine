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

from omero_search_engine.cache_functions.elasticsearch.elasticsearch_templates import (  # noqa
    image_template,
    key_values_resource_cache_template,
)

from omero_search_engine.validation.results_validator import (
    Validator,
    check_number_images_sql_containers_using_ids,
)
from omero_search_engine.cache_functions.elasticsearch.transform_data import (
    delete_es_index,
    create_index,
    get_all_indexes_from_elasticsearch,
)
from test_data import (
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
    images_keys,
    images_value_parts,
    contains_not_contains_queries,
    image_owner,
    image_group,
    image_owner_group,
)

from omero_search_engine import search_omero_app, create_app

create_app("testing")
# deep_check should be a configuration item
deep_check = True


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
        table = "image1"
        es_index = "image_keyvalue_pair_metadata_1"
        es_index_2 = "key_values_resource_cach"
        create_es_index_2 = True
        all_all_indices = get_all_indexes_from_elasticsearch()
        if es_index_2 in all_all_indices.keys():
            create_es_index_2 = False

        if es_index not in all_all_indices.keys():
            self.assertTrue(create_index(es_index, image_template))
        if create_es_index_2:
            self.assertTrue(
                create_index(es_index_2, key_values_resource_cache_template)
            )
        res = search_resource_annotation(table, query)
        assert len(res.get("results")) >= 0
        self.assertTrue(delete_es_index(es_index))
        if create_es_index_2:
            self.assertTrue(delete_es_index(es_index_2))

    def test_single_query(self):
        """
        test query the search engine and compare
        its results with the results from the database
        """
        for resource, cases in simple_queries.items():
            for case in cases:
                name = case[0]
                value = case[1]
                validator = Validator(deep_check)
                validator.set_simple_query(resource, name, value)
                validator.get_results_db("equals")
                validator.get_results_searchengine("equals")
                self.assertEqual(
                    len(validator.postgres_results),
                    validator.searchengine_results.get("size"),
                )
                validator.get_results_db("not_equals")
                validator.get_results_searchengine("not_equals")
                self.assertEqual(
                    len(validator.postgres_results),
                    validator.searchengine_results.get("size"),
                )
                self.assertTrue(validator.identical)

    def test_and_query(self):
        name = "query_image_and"
        for cases in query_image_and:
            validator = Validator(deep_check)
            validator.set_complex_query(name, cases)
            validator.compare_results()
            self.assertEqual(
                len(validator.postgres_results),
                validator.searchengine_results.get("size"),
            )
            self.assertTrue(validator.identical)

    def test_or_query(self):
        name = "query_image_or"
        for cases in query_image_or:
            validator = Validator(deep_check)
            validator.set_complex_query(name, cases)
            validator.compare_results()
            self.assertEqual(
                len(validator.postgres_results),
                validator.searchengine_results.get("size"),
            )
            self.assertTrue(validator.identical)

    def test_no_images_containers(self):
        self.assertTrue(check_number_images_sql_containers_using_ids())

    def test_multi_or_quries(self):
        pass

    def test_complex_query(self):
        name = "query_image_and_or"
        for cases in query_image_and_or:
            validator = Validator(deep_check)
            validator.set_complex_query(name, cases)
            validator.compare_results()
            self.assertEqual(
                len(validator.postgres_results),
                validator.searchengine_results.get("size"),
            )
            self.assertTrue(validator.identical)

    def test_in_query(self):
        for resource, cases in query_in.items():
            for case in cases:
                validator = Validator(deep_check)
                validator.set_in_query(case, resource)
                validator.compare_results()
                self.assertEqual(
                    len(validator.postgres_results),
                    validator.searchengine_results.get("size"),
                )
                self.assertTrue(validator.identical)

    def test_not_in_query(self):
        for resource, cases in query_in.items():
            for case in cases:
                validator = Validator(deep_check)
                validator.set_in_query(case, resource, type="not_in_clause")
                validator.compare_results()
                self.assertEqual(
                    len(validator.postgres_results),
                    validator.searchengine_results.get("size"),
                )
                self.assertTrue(validator.identical)

    def test_seach_for_any_value(self):
        for part in images_value_parts:
            validator = Validator(deep_check)
            validator.set_simple_query("image", None, part, type="buckets")
            validator.compare_results()
            self.assertEqual(
                len(validator.postgres_results),
                validator.searchengine_results.get("total_number_of_buckets"),
            )

    def test_available_values_for_key(self):
        for image_key in images_keys:
            validator = Validator(deep_check)
            validator.set_simple_query("image", image_key, None, type="buckets")
            validator.compare_results()
            self.assertEqual(
                len(validator.postgres_results),
                validator.searchengine_results.get("total_number_of_buckets"),
            )

    def test_contains_not_contains_queries(self):
        for resource, cases in contains_not_contains_queries.items():
            for case in cases:
                name = case[0]
                value = case[1]
                validator = Validator(deep_check)
                validator.set_contains_not_contains_query(resource, name, value)
                validator.get_results_db("contains")
                validator.get_results_searchengine("contains")
                self.assertEqual(
                    len(validator.postgres_results),
                    validator.searchengine_results.get("size"),
                )
                validator.get_results_db("not_contains")
                validator.get_results_searchengine("not_contains")
                self.assertEqual(
                    len(validator.postgres_results),
                    validator.searchengine_results.get("size"),
                )
                self.assertTrue(validator.identical)

    def test_owner(self):
        for resource, cases in image_owner.items():
            for case in cases:
                name = case[0]
                value = case[1]
                owner_id = case[2]
                validator = Validator(deep_check)
                validator.set_simple_query(resource, name, value)
                validator.set_owner_group(owner_id=owner_id)
                validator.compare_results()
                self.assertEqual(
                    len(validator.postgres_results),
                    validator.searchengine_results.get("size"),
                )

    def test_group(self):
        for resource, cases in image_group.items():
            for case in cases:
                name = case[0]
                value = case[1]
                group_id = case[2]
                validator = Validator(deep_check)
                validator.set_simple_query(resource, name, value)
                validator.set_owner_group(group_id=group_id)
                validator.compare_results()
                self.assertEqual(
                    len(validator.postgres_results),
                    validator.searchengine_results.get("size"),
                )

    def test_owner_group(self):
        for resource, cases in image_owner_group.items():
            for case in cases:
                name = case[0]
                value = case[1]
                owner_id = case[2]
                group_id = case[3]
                validator = Validator(deep_check)
                validator.set_simple_query(resource, name, value)
                validator.set_owner_group(owner_id=owner_id, group_id=group_id)
                validator.compare_results()
                self.assertEqual(
                    len(validator.postgres_results),
                    validator.searchengine_results.get("size"),
                )

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
