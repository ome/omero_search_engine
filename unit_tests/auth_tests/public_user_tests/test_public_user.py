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

from flask import g


from omero_search_engine.cache_functions.elasticsearch.elasticsearch_templates import (  # noqa
    image_template,
    key_values_resource_cache_template,
)

from omero_search_engine.validation.results_validator import (
    Validator,
    # test_csv_data_sources,
    # check_number_images_sql_containers_using_ids,
)

from omero_search_engine.api.auth.utils import (
    check_token,
    build_token,
    get_public_user_details,
)

from unit_tests.test_data import (
    simple_queries,
    data_source,
    public_user,
    public_user_data,
)

from omero_search_engine import create_app

create_app("testing")
# deep_check should be a configuration item
deep_check = False

# for data_source in search_omero_app.config.database_connectors.keys():


class BasicTestCase(unittest.TestCase):
    def setUp(self):
        self.data_source = data_source

    def test_create_public_token(self):
        session_id, public_username, public_user_password = get_public_user_details(
            self.data_source
        )
        self.assertEqual(public_user, public_username)
        token = build_token(public_user_data, public_username)
        check = check_token(token, check_session=False)
        self.assertTrue(check.get(self.data_source).get("is_valid"))

    def test_query_with_public_user(self):
        """
        test user who has permission to access the images in the query results
        """
        session_id, public_username, public_user_password = get_public_user_details(
            self.data_source
        )
        token = build_token(public_user_data, public_username)
        check = check_token(token, check_session=False)
        g.token = check
        resource = "image"
        name = simple_queries[resource][0][0]
        value = simple_queries["image"][0][0]
        validator = Validator(self.data_source, deep_check)
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
            12475,
            validator.searchengine_results.get("size"),
        )
        self.assertTrue(validator.identical)

    def test_another_query_public_user(self):
        """
        test user who does not have permission to access the images in the query results
        """
        session_id, public_username, public_user_password = get_public_user_details(
            self.data_source
        )
        token = build_token(public_user_data, public_username)
        check = check_token(token, check_session=False)
        g.token = check
        resource = "image"
        name = simple_queries[resource][0][0]
        value = simple_queries["image"][0][0]
        validator = Validator(self.data_source, deep_check)
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
            12475,
            validator.searchengine_results.get("size"),
        )
        self.assertTrue(validator.identical)
