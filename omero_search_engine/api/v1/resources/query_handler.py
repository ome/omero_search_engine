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
from omero_search_engine.api.v1.resources.urls import (
    search_resource_annotation,
    get_resource_names,
)
import json
from jsonschema import validate, ValidationError, SchemaError, RefResolver
from os.path import abspath, dirname
from pathlib import Path
import os
from urllib.parse import urljoin

# "Name (IDR number)"
mapping_names = {
    "project": {"name": "name", "description": "description"},
    "screen": {"name": "name", "description": "description"},
}

res_and_main_attributes = None
res_or_main_attributes = None
data_sources = []


def reset_global_values():
    global res_and_main_attributes, res_or_main_attributes, data_sources
    res_and_main_attributes = None
    res_or_main_attributes = None
    data_sources = []


def check_get_names(idr_, resource, attribute, data_source, return_exact=False):
    # check the idr name and return the resource and possible values
    global data_sources
    if idr_:
        idr_ = idr_.strip()
    pr_names = get_resource_names(resource)
    pr_names = get_resource_names(resource=resource)
    all_act_names = []
    if pr_names:
        if not return_exact:
            for data_source_, pr_names_ in pr_names.items():
                if (
                    data_source
                    and data_source != "all"
                    and data_source_.lower() not in data_source
                ):
                    continue
                act_name = [
                    {"id": name["id"], "data_source": data_source_}
                    for name in pr_names_
                    if name[attribute] and idr_.lower() in name[attribute].lower()
                ]
                all_act_names = all_act_names + act_name
        else:
            # This should be modified to query a specific data source
            for data_source_, pr_names_ in pr_names.items():
                if (
                    data_source
                    and data_source != "all"
                    and data_source_.lower() not in data_source
                ):
                    continue
                act_name = [
                    {"id": name["id"], "data_source": data_source_}
                    for name in pr_names_
                    if name[attribute] and idr_.lower() in name[attribute].lower()
                ]
                all_act_names = all_act_names + act_name
        returned_act_names = []
        for act in all_act_names:
            returned_act_names.append(act["id"])
            if act["data_source"] not in data_sources:
                data_sources.append(act["data_source"])

        return returned_act_names


class QueryItem(object):
    def __init__(self, filter, data_source, adjust_res=True):
        """
        define query and adjust resource if it is needed,
        e.g. name is provided
        Args:
            resource:
            attribute_name:
            attribute_value:
            operator:
        """
        self.resource = filter.get("resource")
        self.name = filter.get("name")
        self.value = filter.get("value")
        self.operator = filter.get("operator")
        self.data_source = data_source
        self.org_type = filter.get("org_type")
        if filter.get("set_query_type") and filter.get("query_type"):
            self.query_type = filter.get("query_type")
        else:
            self.query_type = "keyvalue"

        if adjust_res:
            self.adjust_resource()
        # it will be used when buildingthe query

    def adjust_resource(self):
        # if self.resource != "image":#in mapping_names :
        # test if the resource is in the attribute name mapping dict
        # if so, it will check if its attribute name is inside the dict
        # to use the actual attribute name
        if mapping_names.get(self.resource):
            if mapping_names[self.resource].get(self.name):
                self.name = mapping_names[self.resource].get(self.name)
                if self.operator == "contains" or self.operator == "not_contains":
                    ac_value = check_get_names(
                        self.value, self.resource, self.name, self.data_source
                    )
                    if len(ac_value) == 0:
                        self.value = -1
                    elif len(ac_value) == 1:
                        self.value = ac_value[0]
                    elif len(ac_value) > 1:
                        self.value = ac_value
                    if self.operator == "contains":
                        self.operator = "equals"
                    else:
                        self.operator = "not_equals"
                else:
                    ac_value = check_get_names(
                        self.value, self.resource, self.name, self.data_source, True
                    )
                    if ac_value and len(ac_value) == 1:
                        self.value = ac_value[0]
                    elif not ac_value or len(ac_value) == 0:
                        self.value = -1
                    else:
                        self.value = ac_value
                """
                pr_names = get_resource_names(self.resource)
                if not self.value in pr_names:
                    # Assuming that the resource is either project or screen
                    self.resource="screen"
                self.name=mapping_names[self.resource].get(self.name)
                """
                self.query_type = "main_attribute"


class QueryGroup(object):
    """
    query list is used to check and adjust multiple resources queries
    """

    def __init__(self, group_type):
        self.query_list = []
        self.group_type = group_type
        self.resources_query = {}
        self.main_attribute = {}
        self.resource = []

    def add_query(self, query):
        self.query_list.append(query)

    def divide_filter(self):
        for filter in self.query_list:
            if filter.resource not in self.resources_query:
                flist = []
                self.resources_query[filter.resource] = flist
            else:
                flist = self.resources_query[filter.resource]
            flist.append(filter)
            self.resource = self.resources_query.keys()

    def adjust_query_main_attributes(self):
        if self.group_type == "and_filters":
            main_type = "and_main_attributes"
        else:
            main_type = "or_main_attributes"
        to_be_removed = {}
        for resource, queries in self.resources_query.items():
            for query in queries:
                if query.query_type == "main_attribute":
                    if resource not in self.main_attribute:
                        self.main_attribute[resource] = {main_type: [query]}
                    else:
                        self.main_attribute[resource][main_type].append(query)
                    if resource not in to_be_removed:
                        to_be_removed[resource] = [query]
                    else:
                        to_be_removed[resource].append(query)

        for resource, queries in to_be_removed.items():
            for query in queries:
                self.resources_query[resource].remove(query)


class QueryRunner(
    object,
):
    """
    Run the queries and return the results
    """

    def __init__(
        self,
        and_query_group,
        or_query_group,
        case_sensitive,
        bookmark,
        pagination_dict,
        raw_elasticsearch_query,
        columns_def,
        return_columns,
        return_containers,
        data_source,
    ):
        self.or_query_group = or_query_group
        self.and_query_group = and_query_group
        self.case_sensitive = case_sensitive
        self.bookmark = bookmark
        self.pagination_dict = pagination_dict
        self.columns_def = columns_def
        self.raw_elasticsearch_query = raw_elasticsearch_query
        self.image_query = {}
        self.additional_image_conds = []
        self.return_columns = return_columns
        self.return_containers = return_containers
        self.data_source = data_source

    def get_image_non_image_query(self):
        res = None
        image_or_queries = []
        image_and_queries = []
        main_or_attribute = {}
        main_and_attribute = {}
        # check or main attributes
        # then run and add the results (in term of clauses)
        # to the main image query
        for or_it in self.or_query_group:
            checked_list = []
            main_or_attribute_ = {}
            for resource, main in or_it.main_attribute.items():
                checked_list.append(resource)
                query = {}
                query["main_attribute"] = main
                for k, v in main.items():
                    org_type = None
                    for v_ in v:
                        org_type = v_.org_type
                        if org_type:
                            break
                    if org_type:
                        break
                res = self.run_query(query, resource)
                new_cond = get_ids(res, resource, self.data_source, org_type)
                if new_cond:
                    if not main_or_attribute_.get(resource):
                        main_or_attribute_[resource] = new_cond
                    else:
                        main_or_attribute_[resource] = (
                            main_or_attribute_[resource] + new_cond
                        )
                elif len(main_or_attribute_.keys()) == 0 and len(checked_list) == len(
                    or_it.resources_query
                ):
                    return {"Error": "Your query returns no results"}
            for res, items_ in main_or_attribute_.items():
                for it_ in items_:
                    org_type = it_.org_type
                    if org_type:
                        break
                if res not in main_or_attribute:
                    main_or_attribute[res] = items_
                else:
                    main_or_attribute[res] = combine_conds(
                        main_or_attribute[res], items_, res
                    )
        # check or_filters
        for or_it in self.or_query_group:
            checked_list = []
            main_or_attribute_ = {}
            for resource, or_query in or_it.resources_query.items():
                checked_list.append(resource)
                if resource == "image":
                    image_or_queries.append(or_query)
                else:
                    # non image or filters should be inside the or main
                    # attributes filters
                    if len(or_query) == 0:
                        continue
                    query = {}
                    query["or_filters"] = or_query
                    for con_ in or_query:
                        org_type = con_.org_type
                        if org_type:
                            break
                    res = self.run_query(query, resource)
                    if type(res) is str:
                        return res
                    for con_ in or_query:
                        org_type = con_.org_type
                        if org_type:
                            break

                    new_cond = get_ids(res, resource, self.data_source, org_type)
                    if new_cond:
                        if not main_or_attribute_.get(resource):
                            main_or_attribute_[resource] = new_cond
                        else:
                            main_or_attribute_[resource] = (
                                main_or_attribute_[resource] + new_cond
                            )

                        # main_or_attribute.append(new_cond)
                        # self.additional_image_conds.append(new_cond)
                    else:
                        # check if all the conditions have been checked
                        if len(main_or_attribute_.keys()) == 0 and len(
                            checked_list
                        ) == len(or_it.resources_query):
                            return {"Error": "Your query returns no results"}
            for res, items_ in main_or_attribute_.items():
                if res not in main_or_attribute:
                    main_or_attribute[res] = items_
                else:
                    for it_ in items_:
                        org_type = it_.org_type
                        if org_type:
                            break
                    if org_type == "and":
                        #######
                        main_or_attribute[res] = combine_conds(
                            main_or_attribute[res], items_, res
                        )
                    else:
                        main_or_attribute[res] = combine_conditions(
                            main_or_attribute[res], items_, res
                        )
        if len(self.or_query_group) > 0 and len(image_or_queries) == 0:
            no_conds = 0
            for res, item in main_or_attribute.items():
                no_conds += len(item)
            if no_conds == 0:
                return {
                    "Error": "6. Your query returns no results for %s"
                    % self.data_source
                }
        # check and main attributes
        for and_it in self.and_query_group:
            for resource, main in and_it.main_attribute.items():
                query = {}
                query["main_attribute"] = main
                res = self.run_query(query, resource)
                new_cond = get_ids(res, resource, self.data_source, "and")
                if new_cond:
                    if not main_and_attribute.get(resource):
                        main_and_attribute[resource] = new_cond
                    else:
                        main_and_attribute[resource] = combine_conditions(
                            main_and_attribute[resource], new_cond, resource
                        )
                else:
                    return {"Error": "Your query returns no results"}

        # check and_filters
        for and_it in self.and_query_group:
            for resource, and_query in and_it.resources_query.items():
                if resource == "image":
                    image_and_queries.append(and_query)
                else:
                    if len(and_query) == 0:
                        continue
                    query = {}
                    query["and_filters"] = and_query
                    res = self.run_query(query, resource)
                    new_cond = get_ids(res, resource, self.data_source, "and")
                    if new_cond:
                        if not main_and_attribute.get(resource):
                            main_and_attribute[resource] = new_cond
                        else:
                            main_and_attribute[resource] = combine_conditions(
                                main_and_attribute[resource], new_cond, resource
                            )
                    else:
                        return {"Error": "Your query returns no results"}

        for res, main_list in main_and_attribute.items():
            if res in main_or_attribute:
                m_list = combine_conditions(main_list, main_or_attribute[res], res)
                main_or_attribute[res] = m_list
            else:
                main_or_attribute[res] = main_list

        self.image_query["main_attribute"] = {
            "or_main_attributes": list(main_or_attribute.values()),
            "and_main_attributes": [],
        }
        self.image_query["and_filters"] = image_and_queries
        self.image_query["or_filters"] = image_or_queries
        return self.run_query(self.image_query, "image")

    def run_query(self, query_, resource):
        main_attributes = {}
        query = {"and_filters": [], "or_filters": []}
        if query_.get("and_filters"):
            for qu in query_.get("and_filters"):
                if isinstance(qu, list):
                    for qu_ in qu:
                        query.get("and_filters").append(qu_.__dict__)
                else:
                    query.get("and_filters").append(qu.__dict__)

        if query_.get("or_filters"):
            qq = []
            for qu_ in query_.get("or_filters"):
                if isinstance(qu_, list):
                    tmpss = []
                    query.get("or_filters").append(tmpss)
                    for qu in qu_:
                        tmpss.append(qu.__dict__)
                else:
                    if qq not in query.get("or_filters"):
                        query.get("or_filters").append(qq)
                    qq.append(qu_.__dict__)

        if query_.get("main_attribute"):
            for key, qu_items in query_.get("main_attribute").items():
                ss = []
                for qu in qu_items:
                    if not qu:
                        continue
                    if not isinstance(qu, list):
                        ss.append(qu.__dict__)
                    else:
                        bb = []
                        ss.append(bb)
                        for qu__ in qu:
                            # bb=[]
                            # ss.append(bb)
                            if isinstance(qu__, QueryItem):
                                bb.append(qu__.__dict__)
                            elif isinstance(qu__, list):
                                for qu_ in qu__:
                                    bb.append(qu_.__dict__)
                            else:
                                return {"Error": "M"}
                main_attributes[key] = ss
        query["case_sensitive"] = self.case_sensitive
        # if len(query.get("and_filters"))==0 and
        # len(query.get("or_filters"))==0 and
        # len(main_attributes.get("or_main_attributes"))==0 and
        # len(main_attributes.get("and_main_attributes"))==0:
        #    return {"Error": "Your query returns no results"}
        if resource == "image":
            bookmark = self.bookmark
            pagination_dict = self.pagination_dict
        else:
            bookmark = None
            pagination_dict = None

        # res = search_query(query, resource, bookmark,
        #                    self.raw_elasticsearch_query,
        #                    main_attributes,return_containers=self.return_containers)
        global res_and_main_attributes, res_or_main_attributes, data_sources
        if res_and_main_attributes:
            if main_attributes.get("and_main_attributes"):
                main_attributes["and_main_attributes"] = (
                    main_attributes.get("and_main_attributes") + res_and_main_attributes
                )
            else:
                main_attributes["and_main_attributes"] = res_and_main_attributes
        if resource == "image" and self.return_containers:
            if len(data_sources) > 0:
                res = search_query(
                    query,
                    resource,
                    bookmark,
                    pagination_dict,
                    self.raw_elasticsearch_query,
                    main_attributes,
                    return_containers=self.return_containers,
                    # data_source=self.data_source,
                    data_source=",".join(data_sources),
                )
            else:
                res = search_query(
                    query,
                    resource,
                    bookmark,
                    pagination_dict,
                    self.raw_elasticsearch_query,
                    main_attributes,
                    return_containers=self.return_containers,
                    data_source=self.data_source,
                )

        else:
            if len(data_sources) > 0:
                res = search_query(
                    query,
                    resource,
                    bookmark,
                    pagination_dict,
                    self.raw_elasticsearch_query,
                    main_attributes,
                    # data_source=self.data_source,
                    data_source=",".join(data_sources),
                )
            else:
                res = search_query(
                    query,
                    resource,
                    bookmark,
                    pagination_dict,
                    self.raw_elasticsearch_query,
                    main_attributes,
                    data_source=self.data_source,
                )
        if resource != "image":
            return res
        elif self.return_columns:
            return process_search_results(res, "image", self.columns_def)
        else:
            return res


def search_query(
    query,
    resource,
    bookmark,
    pagination_dict,
    raw_elasticsearch_query,
    main_attributes=None,
    return_containers=False,
    data_source=None,
):
    search_omero_app.logger.info(
        "-------------------------------------------------"
    )  # noqa
    # search_omero_app.logger.info("1. query: %s" % query)
    search_omero_app.logger.info("2. main_attributes: %s " % main_attributes)
    search_omero_app.logger.info(resource)
    search_omero_app.logger.info(
        "-------------------------------------------------"
    )  # noqa
    search_omero_app.logger.info(("2: resource: %s, 2: query: %s") % (resource, query))
    if not main_attributes:
        q_data = {"query": {"query_details": query}}
    elif resource == "image":
        q_data = {"query": {"query_details": query, "main_attributes": main_attributes}}
    else:
        q_data = {"query": {"query_details": query, "main_attributes": main_attributes}}
    try:
        if bookmark or pagination_dict:
            q_data["bookmark"] = bookmark
            q_data["pagination"] = pagination_dict
            q_data["raw_elasticsearch_query"] = raw_elasticsearch_query
            ress = search_resource_annotation(
                resource,
                q_data.get("query"),
                raw_elasticsearch_query=raw_elasticsearch_query,
                bookmark=bookmark,
                pagination_dict=pagination_dict,
                return_containers=return_containers,
                data_source=data_source,
            )
        else:
            # Should have a method to search the elasticsearch and
            # returns the containers only,
            # It is hard coded in the util search_annotation method.
            ress = search_resource_annotation(
                resource,
                q_data.get("query"),
                return_containers=return_containers,
                data_source=data_source,
            )
        if type(ress) is str:
            return ress

        ress["Error"] = "none"
        return ress
    except Exception as ex:
        search_omero_app.logger.info("Error: " + str(ex))
        return {
            "Error": "Something went wrong, please try later.\
            If you have this error again, please contact the\
            system administrator."
        }


def combine_conditions(curnt_cond, new_cond, resource):
    returned_cond = []
    cons = []
    for c_cond in curnt_cond:
        cons.append(c_cond.value)
        returned_cond.append(c_cond)
    for cond in new_cond:
        if cond.value not in cons:
            returned_cond.append(cond)
    return returned_cond


def combine_conds(curnt_cond, new_cond, resource):
    returned_cond = []
    cons = []
    for c_cond in curnt_cond:
        cons.append(c_cond.value)
    for cond in new_cond:
        if cond.value in cons:
            returned_cond.append(cond)
    return returned_cond


def get_ids(results, resource, data_source, org_type):
    ids = []
    if (
        isinstance(results, dict)
        and results.get("results")
        and isinstance(results.get("results"), dict)
        and results.get("results").get("results")
    ):
        for item in results["results"]["results"]:
            qur_item = {}
            # ids.append(qur_item)
            qur_item["name"] = "{resource}_id".format(resource=resource)
            qur_item["value"] = item["id"]
            qur_item["operator"] = "equals"
            qur_item["resource"] = resource
            qur_item["org_type"] = org_type
            qur_item_ = QueryItem(qur_item, data_source)
            ids.append(qur_item_)
    else:
        qur_item = {}
        qur_item["name"] = "{resource}_id".format(resource=resource)
        qur_item["value"] = -1
        qur_item["operator"] = "equals"
        qur_item["resource"] = resource
        qur_item_ = QueryItem(qur_item, data_source)
        ids.append(qur_item_)
    return ids


def process_search_results(results, resource, columns_def):
    returned_results = {}

    if not results.get("results") or len(results["results"]) == 0:
        returned_results["Error"] = "Your query returns no results"
        return returned_results
    cols = []
    values = []
    urls = {
        "image": search_omero_app.config.get("IMAGE_URL"),
        "project": search_omero_app.config.get("PROJECT_URL"),
        "screen": search_omero_app.config.get("SCREEN_URL"),
    }
    extend_url = urls.get(resource)
    if not extend_url:
        extend_url = search_omero_app.config.get("RESOURCE_URL")
    names_ids = {}
    for item in results["results"]["results"]:
        value = {}
        values.append(value)
        value["Id"] = item["id"]
        names_ids[value["Id"]] = item.get("name")

        value["Name"] = item.get("name")
        value["Project name"] = item.get("project_name")
        if item.get("screen_name"):
            value["Study name"] = item.get("screen_name")
        elif item.get("project_name"):
            value["Study name"] = item.get("project_name")

        for k in item["key_values"]:
            if k["name"] not in cols:
                cols.append(k["name"])
            if value.get(k["name"]):
                value[k["name"]] = value[k["name"]] + "; " + k["value"]
            else:
                value[k["name"]] = k["value"]

    columns = []
    for col in cols:
        columns.append(
            {
                "id": col,
                "name": col,
                "field": col,
                "hide": False,
                "sortable": True,
            }
        )
    main_cols = []
    if not columns_def:
        columns_def = []
        cols.sort()
        if resource == "image":
            cols.insert(0, "Study name")
            main_cols.append(("Study name"))
        cols.insert(0, "Name")
        main_cols.append(("Name"))
        cols.insert(0, "Id")
        main_cols.append(("Id"))

        for col in cols:
            columns_def.append(
                {
                    "field": col,
                    "hide": False,
                    "sortable": True,
                }
            )
    else:
        for col_def in columns_def:
            if col_def["field"] not in cols:
                cols.append(col_def["field"])
    for val in values:
        if len(val) != len(cols):
            for col in cols:
                if not val.get(col):
                    val[col] = ""
    # print (columns_def)
    returned_results["columns"] = columns
    returned_results["columns_def"] = columns_def
    returned_results["values"] = values
    returned_results["server_query_time"] = results["server_query_time"]
    returned_results["query_details"] = results["query_details"]
    returned_results["bookmark"] = results["results"]["bookmark"]
    returned_results["page"] = results["results"]["page"]
    returned_results["size"] = results["results"]["size"]
    returned_results["total_pages"] = results["results"]["total_pages"]
    returned_results["extend_url"] = extend_url
    returned_results["names_ids"] = names_ids
    returned_results["raw_elasticsearch_query"] = results[
        "raw_elasticsearch_query"
    ]  # noqa
    if len(values) <= results["results"]["size"]:
        returned_results["contains_all_results"] = True
    else:
        returned_results["contains_all_results"] = False
    returned_results["Error"] = results["Error"]
    returned_results["resource"] = results["resource"] + "s"
    return returned_results


def determine_search_results_(
    query_, data_source="all", return_columns=False, return_containers=False
):
    from omero_search_engine.api.v1.resources.utils import build_error_message

    reset_global_values()
    if query_.get("query_details"):
        case_sensitive = query_.get("query_details").get("case_sensitive")
    else:
        case_sensitive = False
    if data_source:
        data_source = data_source.split(",")
    bookmark = query_.get("bookmark")
    pagination_dict = query_.get("pagination")
    raw_elasticsearch_query = query_.get("raw_elasticsearch_query")
    and_filters = query_.get("query_details").get("and_filters")
    or_filters = query_.get("query_details").get("or_filters")
    and_query_groups = []
    main_attributes = query_.get("main_attributes")
    global res_and_main_attributes, res_or_main_attributes
    if main_attributes:
        res_and_main_attributes = main_attributes.get("and_main_attributes")
        res_or_main_attributes = main_attributes.get("or_main_attributes")
    columns_def = query_.get("columns_def")
    or_query_groups = []
    if and_filters and len(and_filters) > 0:
        and_query_group = QueryGroup("and_filters")
        for filter in and_filters:
            q_item = QueryItem(filter, data_source)
            # Check the name value and, if it is a list,
            # it will create a new or filter for them and move it
            # Please note it is working for and filter when there is not
            # identical match for the idr name
            if q_item.query_type == "main_attribute" and (
                filter["name"] == "description"
            ):
                return build_error_message(
                    "This release does not support search by description."
                )
            if q_item.query_type == "main_attribute" and (
                filter["name"] == "name"  # or filter["name"] == "description"
            ):
                if isinstance(q_item.value, list):
                    new_or_filter = []
                    if not or_filters:
                        or_filters = []
                    or_filters.append(new_or_filter)
                    for val in q_item.value:
                        new_fil = {}
                        new_fil["value"] = val
                        new_fil["name"] = "id"
                        new_fil["resource"] = q_item.resource
                        new_fil["operator"] = filter["operator"]
                        new_fil["set_query_type"] = True
                        new_fil["query_type"] = q_item.query_type
                        new_fil["data_source"] = data_source
                        if filter.get("org_type"):
                            new_fil["org_type"] = filter.get("org_type")
                        new_or_filter.append(new_fil)
                else:
                    q_item.name = "id"
                    and_query_group.add_query(q_item)
            else:
                and_query_group.add_query(q_item)
        and_query_group.divide_filter()
        and_query_group.adjust_query_main_attributes()
        and_query_groups.append(and_query_group)
    if or_filters and len(or_filters) > 0:
        for filters_ in or_filters:
            or_query_group = QueryGroup("or_filters")
            or_query_groups.append(or_query_group)
            if isinstance(filters_, list):
                for filter in filters_:
                    q_item = QueryItem(filter, data_source)
                    if (
                        q_item.query_type == "main_attribute"
                        and filter["name"] == "description"
                    ):
                        return build_error_message(
                            "This release does not support search by description."
                        )
                    if q_item.query_type == "main_attribute" and (
                        filter["name"] == "name"  # or filter["name"] == "description"
                    ):
                        if isinstance(q_item.value, list):
                            for val in q_item.value:
                                new_fil = {}
                                new_fil["value"] = val
                                new_fil["name"] = "id"
                                new_fil["resource"] = q_item.resource
                                new_fil["operator"] = filter["operator"]
                                new_fil["set_query_type"] = True
                                new_fil["query_type"] = q_item.query_type
                                if filter.get("org_type"):
                                    new_fil["org_type"] = filter.get("org_type")
                                _q_item = QueryItem(new_fil, data_source)
                                or_query_group.add_query(_q_item)
                        else:
                            q_item.name = "id"
                            or_query_group.add_query(q_item)
                    else:
                        or_query_group.add_query(q_item)
            or_query_group.divide_filter()
            or_query_group.adjust_query_main_attributes()

    query_runner = QueryRunner(
        and_query_groups,
        or_query_groups,
        case_sensitive,
        bookmark,
        pagination_dict,
        raw_elasticsearch_query,
        columns_def,
        return_columns,
        return_containers,
        data_source,
    )
    query_results = query_runner.get_image_non_image_query()
    return query_results


def simple_search(
    key,
    value,
    operator,
    case_sensitive,
    bookmark,
    resource,
    study,
    data_source,
    return_containers=False,
    random_results=0,
):
    reset_global_values()
    if not operator:
        operator = "equals"
    if key:
        and_filters = [
            {"name": key, "value": value, "operator": operator, "resource": resource}
        ]
    else:
        and_filters = [{"value": value, "operator": operator, "resource": resource}]

    query_details = {"and_filters": and_filters}
    if bookmark:
        bookmark = [bookmark]
    query_details["bookmark"] = [bookmark]
    query_details["case_sensitive"] = case_sensitive
    if not study:
        if return_containers:
            from omero_search_engine.api.v1.resources.utils import (
                search_resource_annotation_return_containers_only,
            )

            return search_resource_annotation_return_containers_only(
                {"query_details": query_details},
                data_source,
                None,
                True,
            )
        else:
            return search_resource_annotation(
                resource,
                {"query_details": query_details},
                bookmark=bookmark,
                return_containers=return_containers,
                data_source=data_source,
                random_results=random_results,
            )
    else:
        and_filters.append(
            {
                "name": "name",
                "value": study,
                "operator": "equals",
                "resource": "project",
            }
        )
        if return_containers:
            from omero_search_engine.api.v1.resources.utils import (
                search_resource_annotation_return_containers_only,
            )

            search_resource_annotation_return_containers_only(
                query_details,
                data_source,
                None,
                True,
            )
        else:
            return determine_search_results_(
                {"query_details": query_details}, data_source=data_source
            )


def add_local_schemas_to(resolver, schema_folder, base_uri, schema_ext=".json"):
    """Add local schema instances to a resolver schema cache.

    Arguments:
        resolver (jsonschema.RefResolver): the reference resolver
        schema_folder (str): the local folder of the schemas.
        base_uri (str): the base URL that you actually use in your '$id' tags
            in the schemas
        schema_ext (str): filter files with this extension in the schema_folder
    """
    for dir, _, files in os.walk(schema_folder):
        for file in files:
            if file.endswith(schema_ext):
                schema_path = Path(dir) / Path(file)
                rel_path = schema_path.relative_to(schema_folder)
                with open(schema_path) as schema_file:
                    schema_doc = json.load(schema_file)
                key = urljoin(base_uri, str(rel_path))
                resolver.store[key] = schema_doc


def query_validator(query):
    main_dir = os.path.abspath(os.path.dirname(__file__))
    query_schema_file = os.path.join(main_dir, "schemas", "query_data.json")
    base_uri = "file:" + abspath("") + "/"
    with open(query_schema_file, "r") as schema_f:
        query_schema = json.loads(schema_f.read())

    resolver = RefResolver(referrer=query_schema, base_uri=base_uri)
    schema_folder = dirname(query_schema_file)
    # schema_folder = Path('omero_search_engine/api/v1/resources/schemas')
    add_local_schemas_to(resolver, schema_folder, base_uri)

    try:
        validate(query, query_schema, resolver=resolver)
        search_omero_app.logger.info("Data is valid")
        return "OK"
    except SchemaError as e:
        search_omero_app.logger.info("there is a schema error")
        search_omero_app.logger.info(e.message)
        return e.message
    except ValidationError as e:
        search_omero_app.logger.info("there is a validation error")
        search_omero_app.logger.info(e.message)
        return e.message
