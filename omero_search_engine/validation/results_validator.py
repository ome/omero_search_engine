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

from omero_search_engine import search_omero_app
import json
from datetime import datetime
from omero_search_engine.api.v1.resources.query_handler import (
    determine_search_results_,
    query_validator,
    simple_search,
)

from omero_search_engine.api.v1.resources.resource_analyser import (
    search_value_for_resource,
    get_key_values_return_contents,
)

from omero_search_engine.validation.psql_templates import (
    query_images_key_value,
    query_image_project_meta_data,
    query_images_screen_key_value,
    query_images_in_project_name,
    query_images_screen_name,
    query_image_in,
    screens_count,
    projects_count,
    query_images_available_values_for_key,
    query_images_any_value,
    query_images_contains_not_contains,
    query_images_in_project_id,
    query_images_in_screen_id,
)
import os

query_methods = {
    "image": query_images_key_value,
    "project": query_image_project_meta_data,
    "screen": query_images_screen_key_value,
    "project_name": query_images_in_project_name,
    "screen_name": query_images_screen_name,
    "query_image_or": query_image_in,
    "in_clause": query_image_in,
    "not_in_clause": query_image_in,
    "screens_count": screens_count,
    "projects_count": projects_count,
    "available_values_for_key": query_images_available_values_for_key,
    "search_any_value": query_images_any_value,
    "image_contains_not_contains": query_images_contains_not_contains,
}


class Validator(object):
    """
    Compare the results which are coming from postgresql server
    and from the searchengine
    """

    def __init__(self, deep_check=False):
        self.deep_check = deep_check
        self.identical = True

    def set_simple_query(self, resource, name, value, type="keyvalue"):
        """
        simple query
        """
        self.resource = resource
        self.type = type
        self.name = name
        self.value = value
        self.postgres_results = []
        self.sql_statement = query_methods[resource]
        self.searchengine_results = {}

    def set_contains_not_contains_query(self, resource, name, value, type="keyvalue"):
        """
        simple query
        """
        self.resource = resource
        self.type = type
        self.name = name
        self.value = value
        self.postgres_results = []
        self.sql_statement = query_methods["image_contains_not_contains"]
        self.searchengine_results = {}

    def set_owner_group(self, owner_id=None, group_id=None):
        self.owner_id = owner_id
        self.group_id = group_id

    def set_in_query(self, clauses, resource="image", type="in_clause"):
        """
        in list query
        """
        self.type = type
        self.clauses = clauses
        self.resource = resource

    def set_complex_query(self, name, clauses, resource="image", type="complex"):
        """
        complex query
        """
        self.resource = resource
        self.clauses = clauses
        self.name = name
        self.value = clauses
        self.type = type
        self.postgres_results = []
        self.searchengine_results = {}

    def get_in_sql(self, clauses, name="in_clause"):
        names = "'%s'" % clauses[0].lower()
        cases = [c.lower() for c in clauses[1]]
        values = "'" + "','".join(cases) + "'"
        if name == "in_clause":
            sql = query_methods[name].substitute(
                names=names, values=values, operator="in"
            )
        elif name == "not_in_clause":
            sql = query_methods[name].substitute(
                names=names, values=values, operator="not in"
            )
        # sql = query_methods[name].substitute(names=names, values=values)
        conn = search_omero_app.config["database_connector"]
        postgres_results = conn.execute_query(sql)
        results = [item["id"] for item in postgres_results]
        search_omero_app.logger.info(
            "results for 'or' received %s" % len(results)
        )  # noqa
        return results

    def get_or_sql(self, clauses, name="query_image_or"):
        names = ""
        values = ""
        for claus in clauses:
            if names:
                names = names + ",'%s'" % claus[0].lower()
                values = values + ",'%s'" % claus[1].lower()
            else:
                names = "'%s'" % claus[0].lower()
                values = "'%s'" % claus[1].lower()
        # sql = query_methods[name].substitute(names=names, values=values)
        sql = query_methods[name].substitute(names=names, values=values, operator="in")
        conn = search_omero_app.config["database_connector"]
        statement_timeout = search_omero_app.config["STATEMENT_TIMEOUT"]
        postgres_results = conn.execute_query(sql, statement_timeout=statement_timeout)

        results = [item["id"] for item in postgres_results]
        search_omero_app.logger.info(
            "results for 'or' received %s" % len(results)
        )  # noqa
        return results

    def get_and_sql(self, clauses):
        results = []
        co = 0
        for claus in clauses:
            sql = query_methods["image"].substitute(
                # toz
                operator="=",
                name=claus[0].lower(),
                value=claus[1].lower(),
            )
            conn = search_omero_app.config["database_connector"]
            statement_timeout = search_omero_app.config["STATEMENT_TIMEOUT"]
            postgres_results = conn.execute_query(
                sql, statement_timeout=statement_timeout
            )
            res = [item["id"] for item in postgres_results]
            search_omero_app.logger.info("results for 'and' received %s" % len(res))
            if co == 0:
                results = res
            else:
                results = list(set(results) & set(res))
            co += 1
        return results

    def get_results_db(self, operator=None):
        """
        Query the postgresql
        """
        search_omero_app.logger.info("Getting results from postgres")
        if self.type == "buckets":
            if self.name:
                sql = query_methods["available_values_for_key"].substitute(
                    name=self.name
                )
                conn = search_omero_app.config["database_connector"]
                self.postgres_results = conn.execute_query(sql)
            elif self.value:
                sql = query_methods["search_any_value"].substitute(val_part=self.value)
                conn = search_omero_app.config["database_connector"]
                self.postgres_results = conn.execute_query(sql)
            return
        if self.type == "in_clause":
            self.postgres_results = self.get_in_sql(self.clauses)
            return
        elif self.type == "not_in_clause":
            self.postgres_results = self.get_in_sql(self.clauses, self.type)
            return
        elif self.type == "complex":
            if self.name == "query_image_or":
                self.postgres_results = self.get_or_sql(self.clauses)
            elif self.name == "query_image_and":
                self.postgres_results = self.get_and_sql(self.clauses)
            else:
                for name, clauses in self.clauses.items():
                    if name == "query_image_or":
                        or_postgres_results = self.get_or_sql(clauses)
                    elif name == "query_image_and":
                        and_postgres_results = self.get_and_sql(clauses)
                self.postgres_results = list(
                    set(or_postgres_results) & set(and_postgres_results)
                )
            return
        else:
            if not operator or operator == "equals":
                operator = "="
            elif operator == "not_equals":
                operator = "!="
            elif operator == "contains":
                operator = "like"
            elif operator == "not_contains":
                operator = "not like"

            if self.name != "name":
                sql = self.sql_statement.substitute(
                    # toz
                    operator=operator,
                    name=self.name.lower(),
                    value=self.value.lower(),
                )
            else:
                sql = self.sql_statement.substitute(name=self.value, operator=operator)

            if hasattr(self, "owner_id") and self.owner_id:
                sql = sql + " and %s.owner_id=%s" % (self.resource, self.owner_id)
            if hasattr(self, "group_id") and self.group_id:
                sql = sql + " and %s.group_id=%s" % (self.resource, self.group_id)
                print(sql)
        # search_omero_app.logger.info ("sql: %s"%sql)
        conn = search_omero_app.config["database_connector"]
        statement_timeout = search_omero_app.config["STATEMENT_TIMEOUT"]
        postgres_results = conn.execute_query(sql, statement_timeout=statement_timeout)
        self.postgres_results = [item["id"] for item in postgres_results]
        search_omero_app.logger.info(
            "results received %s" % len(self.postgres_results)
        )  # noqa

    def get_results_searchengine(self, operator=None):
        """
        Query the results from the serachengine
        """
        if self.type == "buckets":
            if self.name:
                res = get_key_values_return_contents(self.name, "image", False)
                self.searchengine_results = json.loads(res.data)
            elif self.value:
                self.searchengine_results = search_value_for_resource(
                    "image", self.value
                )
            return

        if self.type == "in_clause":
            filters = []
            filters.append(
                {
                    "name": self.clauses[0],
                    "value": self.clauses[1],
                    "operator": "in",
                    "resource": self.resource,
                }
            )
            query = {"and_filters": filters, "or_filters": []}

        elif self.type == "not_in_clause":
            filters = []
            filters.append(
                {
                    "name": self.clauses[0],
                    "value": self.clauses[1],
                    "operator": "not_in",
                    "resource": self.resource,
                }
            )
            query = {"and_filters": filters, "or_filters": []}

        elif self.type == "complex":
            filters = []
            if self.name != "query_image_and_or":
                for claus in self.clauses:
                    filters.append(
                        {
                            "name": claus[0],
                            "value": claus[1],
                            "operator": "equals",
                            "resource": self.resource,
                        }
                    )
                if self.name == "query_image_or":
                    query = {"and_filters": [], "or_filters": [filters]}
                elif self.name == "query_image_and":
                    query = {"and_filters": filters, "or_filters": []}
            else:
                query = {}
                or_filters = []
                query["or_filters"] = or_filters
                for filter_name, clauses in self.clauses.items():
                    filters = []
                    if filter_name == "query_image_or":
                        or_filters.append(filters)
                    else:
                        query["and_filters"] = filters
                    for claus in clauses:
                        filters.append(
                            {
                                "name": claus[0],
                                "value": claus[1],
                                "operator": "equals",
                                "resource": self.resource,
                            }
                        )
        else:
            if not operator:
                operator = "equals"
            if self.name != "name":
                and_filters = [
                    {
                        "name": self.name.lower(),
                        "value": self.value.lower(),
                        "operator": operator,
                        "resource": self.resource,
                    }
                ]
            else:
                and_filters = [
                    {
                        "name": "name",
                        "value": self.value,
                        "resource": "project",
                        "operator": operator,
                    }
                ]
            query = {"and_filters": and_filters, "or_filters": []}
        and_main_attributes = []
        if hasattr(self, "owner_id") and self.owner_id:
            and_main_attributes.append(
                {"name": "owner_id", "value": self.owner_id, "operator": "equals"}
            )
        if hasattr(self, "group_id") and self.group_id:
            and_main_attributes.append(
                {"name": "group_id", "value": self.group_id, "operator": "equals"}
            )
        main_attributes = {"and_main_attributes": and_main_attributes}
        query_data = {"query_details": query, "main_attributes": main_attributes}
        # validate the query syntex
        query_validation_res = query_validator(query_data)
        if query_validation_res == "OK":
            search_omero_app.logger.info("Getting results from search engine")
            searchengine_results = determine_search_results_(query_data)
            if searchengine_results.get("results"):
                size = searchengine_results.get("results").get("size")
                ids = [
                    item["id"]
                    for item in searchengine_results["results"]["results"]  # noqa
                ]
                idsp = [
                    item["id"]
                    for item in searchengine_results["results"]["results"]  # noqa
                ]
            else:
                size = 0
                ids = []
                idsp = []

                # get all the results if the total number is bigger
                # than the page size
            if size >= search_omero_app.config["PAGE_SIZE"] and self.deep_check:
                bookmark = searchengine_results["results"]["bookmark"]
                pagination_dict = searchengine_results["results"]["pagination"]
                # check getting the results using bookmark
                while len(ids) < size:
                    search_omero_app.logger.info(
                        "Received %s/%s" % (len(ids), size)
                    )  # noqa
                    query_data_ = {"query_details": query, "bookmark": bookmark}
                    searchengine_results_ = determine_search_results_(
                        query_data_
                    )  # noqa
                    ids_ = [
                        item["id"]
                        for item in searchengine_results_["results"]["results"]
                    ]
                    ids = ids + ids_
                    bookmark = searchengine_results_["results"]["bookmark"]
                # check the results using pagination
                query_data_ = {"query_details": query, "bookmark": None}
                next_page = pagination_dict.get("next_page")
                while next_page:
                    query_data_ = {
                        "query_details": query,
                        "pagination": pagination_dict,
                    }
                    searchengine_results_ = determine_search_results_(
                        query_data_
                    )  # noqa
                    ids_ = [
                        item["id"]
                        for item in searchengine_results_["results"]["results"]
                    ]
                    idsp = idsp + ids_
                    pagination_dict = searchengine_results["results"]["pagination"]
                    next_page = pagination_dict.get("next_page")
                if len(ids) != len(idsp):
                    search_omero_app.logger.info(
                        "The results using bookmark (%s)  and the "
                        "results using pagination (%s) are not equal"
                        % (len(ids), len(idsp))
                    )

            self.searchengine_results = {"size": size, "ids": ids, "idsp": idsp}

            search_omero_app.logger.info(
                "no of received results from searchengine  : %s"
                % self.searchengine_results.get("size")
            )

        else:
            search_omero_app.logger.info("The query is not valid")

    def get_containers_test_cases(self):
        """
        Compare the results containers from postgres and the searchengine
        """
        mess = []
        mes = "Checking the results containers for name '%s' and value '%s'" % (
            self.name,
            self.value,
        )
        mess.append(mes)
        search_omero_app.logger.info(mes)
        screens_count_sql = query_methods["screens_count"].substitute(
            key=self.name, value=self.value
        )
        projects_count_sql = query_methods["projects_count"].substitute(
            key=self.name, value=self.value
        )
        conn = search_omero_app.config["database_connector"]
        statement_timeout = search_omero_app.config["STATEMENT_TIMEOUT"]
        screens_results = conn.execute_query(
            screens_count_sql, statement_timeout=statement_timeout
        )
        projects_results = conn.execute_query(
            projects_count_sql, statement_timeout=statement_timeout
        )
        screens_results_idr = [item["name"] for item in screens_results]
        projects_results_idr = [item["name"] for item in projects_results]
        search_engine_results = simple_search(
            self.name,
            self.value,
            "equals",
            False,
            None,
            self.resource,
            None,
            return_containers=True,
        )
        # print(search_engine_results["results"])
        if search_engine_results.get("results") and search_engine_results[
            "results"
        ].get("results"):
            for item in search_engine_results["results"].get("results"):
                if item["type"] == "screen":
                    if item["name"] in screens_results_idr:
                        mes = (
                            "Screen %s is found in the PostgreSQL results"
                            % item["name"]
                        )
                        mess.append(mes)
                        search_omero_app.logger.info(mes)
                    else:
                        mes = (
                            "Erro, screen %s is not found in the PostgreSQL results"
                            % item["name"]
                        )
                        mess.append(mes)
                        search_omero_app.logger.info(mes)

                elif item["type"] == "project":
                    if item["name"] in projects_results_idr:
                        mes = (
                            "Project %s is found in the PostgreSQL results"
                            % item["name"]
                        )
                        mess.append(mes)
                        search_omero_app.logger.info(mes)
                    else:
                        mes = (
                            "Error, project %s is not found in the PostgreSQL results"
                            % item["name"]
                        )
                        mess.append(mes)
                        search_omero_app.logger.info(mes)
            no_results_searchengine = len(
                search_engine_results["results"].get("results")
            )
            no_results_postgresql = len(screens_results_idr) + len(projects_results_idr)
            if no_results_postgresql == no_results_searchengine:
                mes = (
                    "The number of the results (containers) from PostgreSQL "
                    "and the Searchengine (%s) are equal" % no_results_postgresql
                )
                mess.append(mes)
                search_omero_app.logger.info(mes)
            else:
                mes = (
                    "Error, the number of the results from PostgreSQL %s "
                    "and the Searchengine %s are not equal"
                    % (no_results_postgresql, no_results_searchengine)
                )
                mess.append(mes)
                search_omero_app.logger.info(mes)
        else:
            mes = "No results found in the Searchengine"
            mess.append(mes)
            search_omero_app.logger.info(mes)
        return mess

    def compare_results(self, operator=None):
        """
        Get and compare the results between the database and the searchengine
        """
        st_time = datetime.now()
        self.get_results_db(operator)
        st2_time = datetime.now()
        self.get_results_searchengine(operator)
        st3_time = datetime.now()
        sql_time = st2_time - st_time
        searchengine_time = st3_time - st2_time
        if self.type == "bucket":
            return

        if len(self.postgres_results) == self.searchengine_results.get("size"):
            is_it_repated = []
            serach_ids = [id for id in self.searchengine_results.get("ids")]
            serach_idsp = [id for id in self.searchengine_results.get("idsp")]
            if self.deep_check:
                if sorted(serach_ids) != sorted(self.postgres_results):
                    self.identical = False
                if sorted(serach_idsp) != sorted(serach_ids):
                    self.identical = False
            else:
                if sorted(serach_idsp) != sorted(serach_ids):
                    self.identical = False
                else:
                    for id in serach_ids:
                        if id in is_it_repated:
                            self.identical = False
                            break
                        else:
                            is_it_repated.append(id)
                        if id not in self.postgres_results:
                            self.identical = False
                            break
            if self.identical:
                search_omero_app.logger.info(
                    "No of the retuned results are similar ..."
                )
                return (
                    "equal (%s images), \n database server query time= %s,"
                    "searchengine query time= %s"
                    % (len(self.postgres_results), sql_time, searchengine_time)
                )
        if self.searchengine_results:
            searchengine_no = self.searchengine_results.get("size")
        else:
            searchengine_no = self.searchengine_results
        return (
            "not equal, the number of results from the database server is: %s and"
            "the number of results from searchengine is %s?,"
            "\ndatabase server query time= %s, searchengine query time= %s"
            % (len(self.postgres_results), searchengine_no, sql_time, searchengine_time)
        )


def validate_queries(json_file, deep_check):
    import json
    import os

    if not os.path.isfile(json_file):
        return "file: %s is not exist" % json_file

    with open(json_file) as json_data:
        test_data = json.load(json_data)

    # Setthe number pf returend results in one call to 10000
    search_omero_app.config["PAGE_SIZE"] = 10000

    test_cases = test_data.get("test_cases")
    complex_test_cases = test_data.get("complex_test_cases")
    query_in = test_data.get("query_in")
    messages = []
    from datetime import datetime

    for resource, cases in test_cases.items():
        for case in cases:
            start_time = datetime.now()
            name = case[0]
            value = case[1]
            search_omero_app.logger.info(
                "Testing (equals) %s for name: %s, key: %s" % (resource, name, value)
            )
            validator = Validator(deep_check)
            validator.set_simple_query(resource, name, value)
            if resource == "image":
                mess = validator.get_containers_test_cases()
                messages = messages + mess
            res = validator.compare_results("equals")
            elabsed_time = str(datetime.now() - start_time)
            messages.append(
                "Results form (equals) the database and search engine"
                "for name: %s , value: %s are: %s"
                % (validator.name, validator.value, res)
            )
            search_omero_app.logger.info("Total time=%s" % elabsed_time)

            # Not equals
            start_time = datetime.now()
            search_omero_app.logger.info(
                "Testing (not equals) %s for name: %s, key: %s"
                % (resource, name, value)
            )
            if resource == "image":
                not_equals_validator = Validator(deep_check)
                not_equals_validator.set_simple_query(resource, name, value)
                res = not_equals_validator.compare_results("not_equals")
                elabsed_time = str(datetime.now() - start_time)
                messages.append(
                    "Results (not_equals) form PostgreSQL and search engine"
                    "for name: %s , value: %s are: %s"
                    % (not_equals_validator.name, not_equals_validator.value, res)
                )
                search_omero_app.logger.info("Total time=%s" % elabsed_time)

    for name, cases_ in complex_test_cases.items():
        for cases in cases_:
            start_time = datetime.now()
            validator_c = Validator(deep_check)
            validator_c.set_complex_query(name, cases)
            res = validator_c.compare_results()
            messages.append(
                "Results from PostgreSQL and search engine for %s name"
                "'%s' and value '%s' are %s"
                % (name, validator_c.name, validator_c.value, res)
            )
            search_omero_app.logger.info(
                "Total time=%s" % str(datetime.now() - start_time)
            )

    for resource, cases in query_in.items():
        for case in cases:
            start_time = datetime.now()
            validator_in = Validator(deep_check)
            validator_in.set_in_query(case, resource)
            res = validator_in.compare_results()
            messages.append(
                "Results for 'in' from the database and search engine"
                "for %s name: %s and value in [%s] are %s"
                % (
                    validator_in.resource,
                    validator_in.clauses[0],
                    ",".join(validator_in.clauses[1]),
                    res,
                )
            )
            end_in = datetime.now()
            search_omero_app.logger.info("Total time=%s" % str(end_in - start_time))
            # test the same but change the operator to not in
            search_omero_app.logger.info("Total time=%s" % str(end_in - start_time))
            validator_not_in = Validator(deep_check)
            validator_not_in.set_in_query(case, resource, type="not_in_clause")
            res = validator_not_in.compare_results()
            messages.append(
                "Results for 'not in' from the database and search engine for %s name: "
                "%s and value in [%s] are %s"
                % (
                    validator_not_in.resource,
                    validator_not_in.clauses[0],
                    ",".join(validator_not_in.clauses[1]),
                    res,
                )
            )
            search_omero_app.logger.info("Total time=%s" % str(datetime.now() - end_in))

    search_omero_app.logger.info(
        "############################################## Check Report ##############################################"  # noqa
    )
    for message in messages:
        search_omero_app.logger.info(message)
        search_omero_app.logger.info(
            "-----------------------------------------------------------------------------"  # noqa
        )
    search_omero_app.logger.info(
        "###########################################################################################################"  # noqa
    )
    # save the check report to a text file
    base_folder = search_omero_app.config.get("BASE_FOLDER")
    if not os.path.isdir(base_folder):
        base_folder = os.path.expanduser("~")

    report_file = os.path.join(base_folder, "check_report.txt")

    report = "\n-----------------------------------------------------------------------------\n".join(  # noqa
        messages
    )
    with open(report_file, "w") as f:
        f.write(report)


def test_no_images():
    idr_url = search_omero_app.config.get("IDR_TEST_FILE_URL")
    if not idr_url:
        return
    if not idr_url:
        search_omero_app.logger.info("No idr test file is found")

    import requests

    response = requests.get(idr_url)
    data = response.text
    lines = []
    for i, line in enumerate(data.split("\n")):
        lines.append(line)
    from omero_search_engine.api.v1.resources.query_handler import (
        determine_search_results_,
    )

    headers = lines[0]
    headers = headers.split("\t")
    for i in range(len(headers) - 1):
        print(i, headers[i])
    names = {}
    for line in lines:
        if lines.index(line) == 0:
            continue
        study = line.split("\t")
        if len(study) == 1:
            continue
        name = "%s/%s" % (study[0], study[1])
        names[name] = int(study[9])

    results = {}
    base_folder = search_omero_app.config.get("BASE_FOLDER")
    if not os.path.isdir(base_folder):
        base_folder = os.path.expanduser("~")

    report_file = os.path.join(base_folder, "check_report.txt")

    report = [
        "\n\n\n======================== Test number of images inside each study ============================\n"  # noqa
    ]
    for name, numbers in names.items():
        or_filters = [
            [
                {
                    "name": "name",
                    "value": name,
                    "operator": "equals",
                    "resource": "screen",
                },
                {
                    "name": "name",
                    "value": name,
                    "operator": "equals",
                    "resource": "project",
                },
            ]
        ]
        and_filters = []
        query = {"and_filters": and_filters, "or_filters": or_filters}
        query_data = {"query_details": query}
        returned_results = determine_search_results_(query_data)
        if returned_results.get("results"):
            if returned_results.get("results").get("size"):
                total_results = returned_results["results"]["size"]
        else:
            total_results = 0
        results[name] = [numbers, total_results]

    for name, result in results.items():
        if result[0] != result[1]:
            message = "Error:%s, results [idr stats, searchengine]: %s" % (name, result)
        else:
            message = "%s is fine, results [idr stats, searchengine]: %s" % (
                name,
                result,
            )
        report.append(message)
    search_omero_app.logger.info(message)
    report = "\n-----------------------------------------------------------------------------\n".join(  # noqa
        report
    )
    with open(report_file, "a") as f:
        f.write(report)

        """print (name, type(names[name]))
    0 Study
    1 Container
    9 5D Images
    12 Size
    """


def get_omero_stats():
    values = ["Attribute", "No. buckets", "Total number", "Resource"]
    base_folder = search_omero_app.config.get("BASE_FOLDER")
    if not os.path.isdir(base_folder):
        base_folder = os.path.expanduser("~")
    stats_file = os.path.join(base_folder, "stats.csv")

    from omero_search_engine.api.v1.resources.resource_analyser import (
        get_restircted_search_terms,
        query_cashed_bucket,
    )

    data = []
    terms = get_restircted_search_terms()
    data.append(",".join(values))
    for resource, names in terms.items():
        for name in names:
            if name == "name":
                continue
            returned_results = query_cashed_bucket(name, resource)
            if resource == "image":
                data.append(
                    "%s, %s, %s,%s"
                    % (
                        name,
                        returned_results.get("total_number_of_buckets"),
                        returned_results.get("total_number_of_image"),
                        resource,
                    )
                )
            else:
                kk = "total_number_of_%s" % resource
                data.append(
                    "%s, %s, %s,%s"
                    % (
                        name,
                        returned_results.get("total_number_of_buckets"),
                        returned_results.get(kk),
                        resource,
                    )
                )

            for dat in returned_results.get("data"):
                if not dat["Value"]:
                    print("Value is empty string", dat["Key"])
    report = "\n".join(data)

    with open(stats_file, "w") as f:
        f.write(report)


def check_number_images_sql_containers_using_ids():
    """
    This method tests the number of images inside each container
     (project or screen) in the searchengine index data
    and compare them with the number of images inside
    each container in the database server.
    As container name is not unique, container id is used
    to determine the number of images
    """
    from omero_search_engine.api.v1.resources.urls import (
        get_resource_names,
    )
    from omero_search_engine.api.v1.resources.utils import (
        search_resource_annotation,
    )

    dd = True

    conn = search_omero_app.config["database_connector"]
    all_names = get_resource_names("all")
    for resource in all_names:
        search_omero_app.logger.info(
            "######################## Checking %s ########################\n" % resource
        )
        for res_name_ in all_names.get(resource):
            res_name = res_name_.get("name")
            res_id = res_name_.get("id")
            search_omero_app.logger.info(
                "Checking %s name: %s, id: %s" % (resource, res_name, res_id)
            )
            and_filters = []
            main_attributes = {
                "and_main_attributes": [
                    {
                        "name": "%s_id" % resource,
                        "value": res_id,
                        "operator": "equals",
                        "resource": "image",
                    }
                ]
            }
            or_filters = []
            query = {"and_filters": and_filters, "or_filters": or_filters}

            query_data = {"query_details": query, "main_attributes": main_attributes}

            returned_results = search_resource_annotation("image", query_data)
            if returned_results.get("results"):
                if returned_results.get("results").get("size"):
                    searchengine_results = returned_results["results"]["size"]
            else:
                searchengine_results = 0
            search_omero_app.logger.info(
                "Number of images returned from searchengine: %s" % searchengine_results
            )
            if resource == "project":
                sql = query_images_in_project_id.substitute(project_id=res_id)
            elif resource == "screen":
                sql = query_images_in_screen_id.substitute(screen_id=res_id)
            results = conn.execute_query(sql)
            postgres_results = len(results)
            search_omero_app.logger.info(
                "Number of images returned from the database: %s" % postgres_results
            )
            if searchengine_results != postgres_results:
                if res_name == "idr0021" and res_id == 872:
                    # """
                    # issue with these two images:
                    # as they belong to two different datasets
                    # image ids= 9539, 9552
                    # """
                    continue
                dd = False
                if searchengine_results > 0:
                    test_array = []
                    for res in returned_results["results"]["results"]:
                        test_array.append(res.get("id"))
                    for ress in results:
                        if ress["id"] not in test_array:
                            print("================>>>>")
                            print(ress["id"])
                    search_omero_app.logger.info("ERROR: Not equal results")
                    print(
                        "Error checking %s name: %s, id: %s"
                        % (resource, res_name, res_id)
                    )
                # return False
            else:
                search_omero_app.logger.info("equal results")
            search_omero_app.logger.info(
                "\n-----------------------------------------------------------------------------\n"  # noqa
            )
    return dd


def get_no_images_sql_containers(write_report=True):
    """
    This method tests the number of images inside each container
     (project or screen) in the searchengine index data
    and compare them with the number of images inside
    each container in the database server
    """
    from omero_search_engine.api.v1.resources.urls import (
        get_resource_names,
    )
    from omero_search_engine.api.v1.resources.utils import adjust_query_for_container

    conn = search_omero_app.config["database_connector"]
    statement_timeout = search_omero_app.config["STATEMENT_TIMEOUT"]

    all_names = get_resource_names("all")
    messages = []
    for resource in all_names:
        messages.append(
            "######################## Checking %s ########################\n" % resource
        )
        for res_name_ in all_names.get(resource):
            res_name = res_name_.get("name")
            message1 = "Checking %s name: %s" % (resource, res_name)
            messages.append(message1)
            search_omero_app.logger.info(message1)

            and_filters = [
                {
                    "name": "name",
                    "value": res_name,
                    "operator": "equals",
                    "resource": "container",
                }
            ]
            or_filters = []
            query = {"and_filters": and_filters, "or_filters": or_filters}
            query_data = {"query_details": query}
            adjust_query_for_container(query_data)
            returned_results = determine_search_results_(query_data)
            if returned_results.get("results"):
                if returned_results.get("results").get("size"):
                    seachengine_results = returned_results["results"]["size"]
            else:
                seachengine_results = 0
            message2 = (
                "No of images returned from searchengine: %s" % seachengine_results
            )
            search_omero_app.logger.info(message2)
            messages.append(message2)
            sql = query_methods["%s_name" % resource].substitute(
                name=res_name, operator="="
            )
            results = conn.execute_query(sql, statement_timeout=statement_timeout)
            postgres_results = len(results)
            message3 = (
                "Number of images returned from the database: %s" % postgres_results
            )
            messages.append(message3)
            search_omero_app.logger.info(message3)
            if seachengine_results != postgres_results:
                message4 = "ERROR: Not equal results"
                messages.append(message4)
                search_omero_app.logger.info(message4)
            else:
                message5 = "equal results"
                messages.append(message5)
                search_omero_app.logger.info(message5)
            messages.append(
                "\n-----------------------------------------------------------------------------\n"  # noqa
            )
    if write_report:
        base_folder = search_omero_app.config.get("BASE_FOLDER")
        if not os.path.isdir(base_folder):
            base_folder = os.path.expanduser("~")
        report_file = os.path.join(base_folder, "check_containers_report.txt")
        report = "\n".join(messages)  # noqa
        with open(report_file, "w") as f:
            f.write(report)


"""
def set_ownership(resource , name, value, owner_id=None, group_id=None):
    if hasattr(self, 'owener_id'):
        if hasattr(self, 'group_id'):
    sql=query_images_key_value.substitute(name=name, value=value)
    if owner_id:
        sql=sql +" %s.%owner_id=%s"%(resource,owner_id)
    if group_id:
        sql = sql + " %s.%group_id=%s" % (resource, group_id)
"""


def check_container_keys_vakues():
    # This will be modified and the testing data will be adjusted and provided
    # at run time
    from omero_search_engine.validation.psql_templates import (
        container_from_name,
        screen_key_values,
        project_key_values,
    )
    import json
    from omero_search_engine.api.v1.resources.resource_analyser import (
        get_container_values_for_key,
    )

    csv = False
    container_names = ["idr0034", "idr0114"]
    keys = ["gene symbol", "cell line"]
    for container_name in container_names:
        for key in keys:
            project_sql = container_from_name.substitute(
                container="project", name=container_name
            )
            screen_sql = container_from_name.substitute(
                container="screen", name=container_name
            )
            conn = search_omero_app.config["database_connector"]
            statement_timeout = search_omero_app.config["STATEMENT_TIMEOUT"]
            project_ids_results = conn.execute_query(
                project_sql, statement_timeout=statement_timeout
            )
            screen_ids_results = conn.execute_query(
                screen_sql, statement_timeout=statement_timeout
            )

            search_omero_app.logger.info("projects: %s" % project_ids_results)
            search_omero_app.logger.info("screens: %s" % screen_ids_results)

            if len(screen_ids_results) > 0:
                for id in screen_ids_results:
                    screen_sql = screen_key_values.substitute(id=id.get("id"), name=key)
                    screen_results = conn.execute_query(
                        screen_sql, statement_timeout=statement_timeout
                    )
                    scr_searchengine_results = get_container_values_for_key(
                        "image", container_name, csv, key
                    )
                    if len(scr_searchengine_results.response) > 0:
                        scr_searchengine_results = json.loads(
                            scr_searchengine_results.response[0]
                        )
                    else:
                        scr_searchengine_results = scr_searchengine_results.response
                    search_omero_app.logger.info(
                        "Results from the database: %s" % len(screen_results)
                    )
                    if len(scr_searchengine_results) > 0 and scr_searchengine_results[
                        0
                    ].get("results"):
                        search_omero_app.logger.info(
                            "Searchengine results: %s"
                            % len(scr_searchengine_results[0].get("results"))
                        )
                    else:
                        search_omero_app.logger.info(
                            "No results returned from searchengine"
                        )
            if len(project_ids_results) > 0:
                for id in project_ids_results:
                    project_sql = project_key_values.substitute(
                        id=id.get("id"), name=key
                    )
                    project_results = conn.execute_query(
                        project_sql, statement_timeout=statement_timeout
                    )
                    pr_searchengine_results = get_container_values_for_key(
                        "image", container_name, csv, key
                    )
                    if len(pr_searchengine_results.response) > 0:
                        pr_searchengine_results = json.loads(
                            pr_searchengine_results.response[0]
                        )
                    else:
                        pr_searchengine_results = pr_searchengine_results.response

                    search_omero_app.logger.info(
                        "Results from the database: %s" % len(project_results)
                    )
                    if len(pr_searchengine_results) > 0 and pr_searchengine_results[
                        0
                    ].get("results"):
                        search_omero_app.logger.info(
                            "Searchengine results: %s "
                            % len(pr_searchengine_results[0].get("results"))
                        )
                    else:
                        search_omero_app.logger.info(
                            "No results returned from searchengine"
                        )
