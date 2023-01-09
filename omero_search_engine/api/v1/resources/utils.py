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

import copy
import os
import sys
import json
from elasticsearch import helpers
import time
from omero_search_engine import search_omero_app
from string import Template
from app_data.data_attrs import annotation_resource_link

main_dir = os.path.abspath(os.path.dirname(__file__))
mm = main_dir.replace("omero_search_engine/api/v2/resources", "")
sys.path.append(mm)


def adjust_value(value):
    """
    Adjust the value to search terms which includes * or ?
    and support search special characters
    """
    if value:
        value = value.strip().strip().lower()
        value = value.translate({ord(c): "\\\\%s" % c for c in "*?&"})
        value = value.translate({ord(c): "\\%s" % c for c in '"'})
    return value


def get_resource_annotation_table(resource_table):
    """
    return the related annotation for the resources table
    it can use annotation_resource_link dict
    """
    if resource_table in annotation_resource_link:
        return annotation_resource_link[resource_table]
    elif resource_table.lower() == "all":
        return annotation_resource_link
    else:
        return None


resource_elasticsearchindex = {
    "project": "project_keyvalue_pair_metadata",
    "screen": "screen_keyvalue_pair_metadata",
    "plate": "plate_keyvalue_pair_metadata",
    "well": "well_keyvalue_pair_metadata",
    "image": "image_keyvalue_pair_metadata",
    # the following index is used for testing purpose only
    "image1": "image_keyvalue_pair_metadata_1",
}

# curl -XPUT -H 'Content-Type: application/json' -d '{"index": {"max_result_window": 20000 }}' 'http://127.0.0.1:9200/image_keyvalue_pair_metadata/_settings' # noqa

range_dict = {
    "gte": ">=",  # "Greater-than or equal to",
    "lte": "<=",  # Less-than or equal to",
    "gt": ">",  # ,"Greater-than",
    "lt": "<",  # "Less-than"
}

"""
The following are the templates which are used at run time to build the query.
Each of them represent Elastic search query template part.

Must ==> AND
must_not ==>  NOT
should ==> OR

"""
# main attribute such as project_id, dataset_id, owner_id,
# group_id, owner_id, etc.
# It supports not two operators, equals and not_equals
main_attribute_query_template = Template(
    """{"bool":{"must":{"match":{"$attribute.keyvalue":"$value"}}}}"""
)
# Search main attribute which has long data type
# ends with "_id" in the image index (template)
main_attribute_query_template_id = Template(
    """
{"bool":{"must":{"match":{"$attribute":"$value"}}}}"""
)

# must_name_condition_template= Template('''{"match": {"key_values.name.keyword":"$name"}}''')  # noqa
# support case_sensitive and case_insensitive for keys
case_sensitive_must_name_condition_template = Template(
    """
{"match": {"key_values.name.keyword":"$name"}}"""
)
case_insensitive_must_name_condition_template = Template(
    """
{"match": {"key_values.name.keynamenormalize":"$name"}}"""
)

case_insensitive_must_value_condition_template = Template(
    """
{"match": {"key_values.value.keyvaluenormalize":"$value"}}"""
)
case_sensitive_must_value_condition_template = Template(
    """
{"match": {"key_values.value.keyvalue":"$value"}}"""
)
nested_keyvalue_pair_query_template = Template(
    """
{"nested": {"path": "key_values",
"query":{"bool": {"must":[$nested ] }}}}"""
)
nested_query_template_must_not = Template(
    """
{"nested": {"path": "key_values",
"query":{"bool": {"must_not":[$must_not_value ]}}}}"""
)
# ==> equal term
must_term_template = Template(""""must" : [$must_term]""")
# ==> not equal
must_not_term_template = Template(""""must_not": [$must_not_term]""")
# Used for contains and not contains
case_sensitive_wildcard_value_condition_template = Template(
    """
{"wildcard": {"key_values.value.keyvalue":"$wild_card_value"}}"""
)

# Used for contains and not contains
case_insensitive_wildcard_value_condition_template = Template(
    """
{"wildcard": {"key_values.value.keyvaluenormalize":"$wild_card_value"}}"""
)
case_sensitive_range_value_condition_template = Template(
    """
{"range":{"key_values.value.keyvalue":{"$operator":"$value"} }}"""
)
case_insensitive_range_value_condition_template = Template(
    """
{"range":{"key_values.value.keyvaluenormalize":{"$operator":"$value"}}}"""
)
should_term_template = Template(
    """
{"bool":{ "should": [$should_term],
"minimum_should_match" : $minimum_should_match ,"boost" : 1.0 }}"""
)  # ==> or


query_template = Template("""{"query": {"bool": {$query}}}""")


# This template is added to the query to return the count of an attribute
count_attr_template = Template(
    """{"key_count": {"terms": {"field": "$field","size": 10000}}}
"""
)

# This template is used to get the study using its idr
res_raw_query = Template(
    """{"query": {"bool": {"must": [{"bool": {"must": {"match":
    {"name.keyvalue": "$idr"}}}}]}}} """
)


def build_error_message(error):
    """
    Build an error respond
    """
    return {"Error": error}


def elasticsearch_query_builder(
    and_filter, or_filters, case_sensitive, main_attributes=None
):
    global nested_keyvalue_pair_query_template
    global must_term_template, must_not_term_template, should_term
    nested_must_part = []
    nested_must_not_part = []
    all_should_part_list = []
    if main_attributes and len(main_attributes) > 0:
        # should_part_list=[]
        # all_should_part_list.append(should_part_list)
        if main_attributes.get("and_main_attributes"):
            for clause in main_attributes.get("and_main_attributes"):
                if isinstance(clause, list):
                    for attribute in clause:
                        if attribute["name"].endswith("_id"):
                            main_dd = (
                                main_attribute_query_template_id.substitute(  # noqa
                                    attribute=attribute["name"].strip(),
                                    value=str(attribute["value"]).strip(),
                                )
                            )
                        else:
                            main_dd = main_attribute_query_template.substitute(
                                attribute=attribute["name"].strip(),
                                value=str(attribute["value"]).strip(),
                            )
                        if attribute["operator"].strip() == "equals":
                            nested_must_part.append(main_dd)
                        elif attribute["operator"].strip() == "not_equals":
                            nested_must_not_part.append(main_dd)
                else:
                    attribute = clause
                    if attribute["name"].endswith("_id"):
                        main_dd = main_attribute_query_template_id.substitute(
                            attribute=attribute["name"].strip(),
                            value=str(attribute["value"]).strip(),
                        )
                    else:
                        main_dd = main_attribute_query_template.substitute(
                            attribute=attribute["name"].strip(),
                            value=str(attribute["value"]).strip(),
                        )
                    if attribute["operator"].strip() == "equals":
                        nested_must_part.append(main_dd)
                    elif attribute["operator"].strip() == "not_equals":
                        nested_must_not_part.append(main_dd)

        if main_attributes.get("or_main_attributes"):
            sh = []
            ssj = {"main": sh}
            all_should_part_list.append(ssj)
            for attributes in main_attributes.get("or_main_attributes"):
                # sh=[]
                # ssj={"main":sh}
                # all_should_part_list.append(ssj)
                if isinstance(attributes, list):
                    for attribute in attributes:
                        # search using id, e.g. project id
                        if attribute["name"].endswith("_id"):
                            main_dd = (
                                main_attribute_query_template_id.substitute(  # noqa
                                    attribute=attribute["name"].strip(),
                                    value=str(attribute["value"]).strip(),
                                )
                            )
                        else:
                            main_dd = main_attribute_query_template.substitute(
                                attribute=attribute["name"].strip(),
                                value=str(attribute["value"]).strip(),
                            )

                        if attribute["operator"].strip() == "equals":
                            sh.append(main_dd)
                        elif attribute["operator"].strip() == "not_equals":
                            sh.append(main_dd)
                else:
                    attribute = attributes
                    # search using id, e.g. project id
                    if attribute["name"].endswith("_id"):
                        main_dd = main_attribute_query_template_id.substitute(
                            attribute=attribute["name"].strip(),
                            value=str(attribute["value"]).strip(),
                        )
                    else:
                        main_dd = main_attribute_query_template.substitute(
                            attribute=attribute["name"].strip(),
                            value=str(attribute["value"]).strip(),
                        )

                    if attribute["operator"].strip() == "equals":
                        sh.append(main_dd)
                    elif attribute["operator"].strip() == "not_equals":
                        sh.append(main_dd)

            # if len(should_part_list)>0:
            #    minimum_should_match=len(should_part_list)

    if and_filter and len(and_filter) > 0:
        for filter in and_filter:
            search_omero_app.logger.info("FILTER %s" % filter)
            try:
                key = filter["name"].strip()
                value = filter["value"].strip()
                operator = filter["operator"].strip()
            except Exception as e:
                search_omero_app.logger.info(str(e))
                return build_error_message(
                    "Each Filter needs to have, name,\
                    value and operator keywords."
                )
            search_omero_app.logger.info("%s %s %s" % (operator, key, value))
            search_omero_app.logger.info("%s %s %s" % (operator, key, value))
            _nested_must_part = []
            if operator == "equals":
                # _nested_must_part.append(must_name_condition_template.substitute(name=key)) # noqa
                if case_sensitive:
                    _nested_must_part.append(
                        case_sensitive_must_value_condition_template.substitute(  # noqa
                            value=value
                        )
                    )
                    _nested_must_part.append(
                        case_sensitive_must_name_condition_template.substitute(
                            name=key
                        )  # noqa
                    )

                else:
                    _nested_must_part.append(
                        case_insensitive_must_value_condition_template.substitute(  # noqa
                            value=value
                        )
                    )
                    _nested_must_part.append(
                        case_insensitive_must_name_condition_template.substitute(  # noqa
                            name=key
                        )
                    )

                nested_must_part.append(
                    nested_keyvalue_pair_query_template.substitute(
                        nested=",".join(_nested_must_part)
                    )
                )
            if operator == "contains":
                value = "*{value}*".format(value=adjust_value(value))
                # _nested_must_part.append(must_name_condition_template.substitute(name=key)) # noqa
                if case_sensitive:
                    _nested_must_part.append(
                        case_sensitive_wildcard_value_condition_template.substitute(  # noqa
                            wild_card_value=value
                        )
                    )
                    _nested_must_part.append(
                        case_sensitive_must_name_condition_template.substitute(
                            name=key
                        )  # noqa
                    )

                else:
                    _nested_must_part.append(
                        case_insensitive_wildcard_value_condition_template.substitute(  # noqa
                            wild_card_value=value
                        )
                    )
                    _nested_must_part.append(
                        case_insensitive_must_name_condition_template.substitute(  # noqa
                            name=key
                        )
                    )

                nested_must_part.append(
                    nested_keyvalue_pair_query_template.substitute(
                        nested=",".join(_nested_must_part)
                    )
                )
            elif operator in ["not_equals", "not_contains"]:
                # nested_must_part.append(nested_keyvalue_pair_query_template.substitute(nested=must_name_condition_template.substitute(name=key)))
                if operator == "not_contains":
                    value = "*{value}*".format(value=adjust_value(value))
                    if case_sensitive:
                        nested_must_part.append(
                            nested_keyvalue_pair_query_template.substitute(
                                nested=case_sensitive_must_name_condition_template.substitute(  # noqa
                                    name=key
                                )
                            )
                        )
                        nested_must_not_part.append(
                            nested_keyvalue_pair_query_template.substitute(
                                nested=case_sensitive_wildcard_value_condition_template.substitute(  # noqa
                                    wild_card_value=value
                                )
                            )
                        )
                    else:
                        nested_must_part.append(
                            nested_keyvalue_pair_query_template.substitute(
                                nested=case_insensitive_must_name_condition_template.substitute(  # noqa
                                    name=key
                                )
                            )
                        )
                        nested_must_not_part.append(
                            nested_keyvalue_pair_query_template.substitute(
                                nested=case_insensitive_wildcard_value_condition_template.substitute(  # noqa
                                    wild_card_value=value
                                )
                            )
                        )

                else:
                    if case_sensitive:
                        nested_must_part.append(
                            nested_keyvalue_pair_query_template.substitute(
                                nested=case_sensitive_must_name_condition_template.substitute(  # noqa
                                    name=key
                                )
                            )
                        )
                        nested_must_not_part.append(
                            nested_keyvalue_pair_query_template.substitute(
                                nested=case_sensitive_must_value_condition_template.substitute(  # noqa
                                    value=value
                                )
                            )
                        )
                    else:
                        nested_must_part.append(
                            nested_keyvalue_pair_query_template.substitute(
                                nested=case_insensitive_must_name_condition_template.substitute(  # noqa
                                    name=key
                                )
                            )
                        )
                        nested_must_not_part.append(
                            nested_keyvalue_pair_query_template.substitute(
                                nested=case_insensitive_must_value_condition_template.substitute(  # noqa
                                    value=value
                                )
                            )
                        )

            elif operator in ["lt", "lte", "gt", "gte"]:
                # nested_must_part.append(nested_keyvalue_pair_query_template.substitute(nested=must_name_condition_template.substitute(name=key))) # noqa
                if case_sensitive:
                    nested_must_part.append(
                        nested_keyvalue_pair_query_template.substitute(
                            nested=case_sensitive_must_name_condition_template.substitute(  # noqa
                                name=key
                            )
                        )
                    )

                    nested_must_part.append(
                        nested_keyvalue_pair_query_template.substitute(
                            nested=case_sensitive_range_value_condition_template.substitute(  # noqa
                                operator=operator, value=value
                            )
                        )
                    )
                else:
                    nested_must_part.append(
                        nested_keyvalue_pair_query_template.substitute(
                            nested=case_insensitive_must_name_condition_template.substitute(  # noqa
                                name=key
                            )
                        )
                    )

                    nested_must_part.append(
                        nested_keyvalue_pair_query_template.substitute(
                            nested=case_insensitive_range_value_condition_template.substitute(  # noqa
                                operator=operator, value=value
                            )
                        )
                    )
    # must_not_term
    if or_filters and len(or_filters) > 0:
        added_keys = []
        co = 0
        for or_filters_ in or_filters:
            co = co + 1
            should_part_list_or = []
            all_should_part_list.append(should_part_list_or)
            for or_filter in or_filters_:
                should_values = []
                shoud_not_value = []
                # should_names = []
                try:
                    key = or_filter["name"].strip()
                    value = or_filter["value"].strip()
                    operator = or_filter["operator"].strip()
                except Exception:
                    return build_error_message(
                        "Each Filter needs to have,\
                        name, value and operator keywords."
                    )

                if key not in added_keys:
                    added_keys.append(key)

                if operator == "equals":
                    if case_sensitive:
                        should_values.append(
                            case_sensitive_must_value_condition_template.substitute(  # noqa
                                value=value
                            )
                        )
                        should_values.append(
                            case_sensitive_must_name_condition_template.substitute(
                                name=key
                            )
                        )
                    else:
                        should_values.append(
                            case_insensitive_must_value_condition_template.substitute(  # noqa
                                value=value
                            )
                        )
                        should_values.append(
                            case_insensitive_must_name_condition_template.substitute(
                                name=key
                            )
                        )
                elif operator == "contains":
                    value = "*{value}*".format(value=value)
                    if case_sensitive:
                        should_values.append(
                            case_sensitive_wildcard_value_condition_template.substitute(  # noqa
                                wild_card_value=value
                            )
                        )
                        should_values.append(
                            case_sensitive_must_name_condition_template.substitute(
                                name=key
                            )
                        )
                    else:
                        should_values.append(
                            case_insensitive_wildcard_value_condition_template.substitute(  # noqa
                                wild_card_value=value
                            )
                        )
                        should_values.append(
                            case_insensitive_must_name_condition_template.substitute(
                                name=key
                            )
                        )
                elif operator in ["not_equals", "not_contains"]:
                    if operator == "not_contains":
                        value = "*{value}*".format(value=value)
                        if case_sensitive:
                            shoud_not_value.append(
                                case_sensitive_wildcard_value_condition_template.substitute(  # noqa
                                    wild_card_value=value
                                )
                            )
                            shoud_not_value.append(
                                case_sensitive_must_name_condition_template.substitute(
                                    name=key
                                )
                            )
                        else:
                            shoud_not_value.append(
                                case_insensitive_wildcard_value_condition_template.substitute(  # noqa
                                    wild_card_value=value
                                )
                            )
                            shoud_not_value.append(
                                case_insensitive_must_name_condition_template.substitute(  # noqa
                                    name=key
                                )
                            )
                    else:
                        if case_sensitive:
                            shoud_not_value.append(
                                case_sensitive_must_value_condition_template.substitute(  # noqa
                                    value=value
                                )
                            )
                            shoud_not_value.append(
                                case_sensitive_must_name_condition_template.substitute(
                                    name=key
                                )
                            )
                        else:
                            shoud_not_value.append(
                                case_insensitive_must_value_condition_template.substitute(  # noqa
                                    value=value
                                )
                            )
                            shoud_not_value.append(
                                case_insensitive_must_name_condition_template.substitute(  # noqa
                                    name=key
                                )
                            )
                elif operator in ["lt", "lte", "gt", "gte"]:
                    if case_sensitive:
                        should_values.append(
                            case_sensitive_range_value_condition_template.substitute(  # noqa
                                operator=operator, value=value
                            )
                        )
                        should_values.append(
                            case_sensitive_must_name_condition_template.substitute(
                                name=key
                            )
                        )
                else:
                    should_values.append(
                        case_insensitive_range_value_condition_template.substitute(  # noqa
                            operator=operator, value=value
                        )
                    )
                    should_values.append(
                        case_insensitive_must_name_condition_template.substitute(
                            name=key
                        )
                    )
                    # must_value_condition
                ss = ",".join(should_values)
                ff = nested_keyvalue_pair_query_template.substitute(nested=ss)
                should_part_list_or.append(ff)
                if len(shoud_not_value) > 0:
                    ss = ",".join(shoud_not_value)
                    ff = nested_query_template_must_not.substitute(must_not_value=ss)
                    should_part_list_or.append(ff)
    all_terms = ""

    for should_part_list_ in all_should_part_list:
        if isinstance(should_part_list_, dict):
            should_part_list = should_part_list_.get("main")
        else:
            should_part_list = should_part_list_

        if len(should_part_list) > 0:

            should_part_ = ",".join(should_part_list)
            should_part_ = should_term_template.substitute(
                should_term=should_part_, minimum_should_match=1
            )
            nested_must_part.append(should_part_)

    if len(nested_must_part) > 0:
        nested_must_part_ = ",".join(nested_must_part)
        nested_must_part_ = must_term_template.substitute(
            must_term=nested_must_part_
        )  # +"%s"%main_dd)

        if all_terms:
            all_terms = all_terms + "," + nested_must_part_
        else:
            all_terms = nested_must_part_

    if len(nested_must_not_part) > 0:

        nested_must_not_part_ = ",".join(nested_must_not_part)
        nested_must_not_part_ = must_not_term_template.substitute(
            must_not_term=nested_must_not_part_
        )

        if all_terms:
            all_terms = all_terms + "," + nested_must_not_part_
        else:
            all_terms = nested_must_not_part_

    return query_template.substitute(query=all_terms)


def check_single_filter(res_table, filter, names, organism_converter):
    key = filter["name"]
    value = filter["value"]
    operator = filter["operator"]
    if operator != "contains" and operator != "not_contains":
        key_ = [name for name in names if name.casefold() == key.casefold()]
        if len(key_) == 1:
            filter["name"] = key_[0]
            if filter["name"] == "Organism":
                vv = [
                    value_
                    for key, value_ in organism_converter.items()
                    if key == value.casefold()
                ]
                if len(vv) == 1:
                    filter["value"] = vv[0]
        else:
            if len(key_) == 0:
                search_omero_app.logger.info("Name Error %s" % str(key))
                return
        from omero_search_engine.api.v1.resources.resource_analyser import (
            get_resource_attribute_values,
        )

        values = get_resource_attribute_values(res_table, key_[0])
        if not values or len(values) == 0:
            search_omero_app.logger.info("Could not check filters %s" % str(filter))
            return
        value_ = [val for val in values if val.casefold() == value.casefold()]
        if len(value_) == 1:
            filter["value"] = value_[0]
        elif len(value_) == 0:
            search_omero_app.logger.info("Value Error: %s/%s" % (str(key), str(value)))


def check_filters(res_table, filters, case_sensitive):
    """
    This method checks the name and value inside the filter and
    fixes if it is not correct, case sensitive error,
    using the general term rather than scientific terms.
    It should be expanded in the future to add more checks and fixes.
    """
    organism_converter = {
        "human": "Homo sapiens",
        "house mouse": "Mus musculus",
        "mouse": "Mus musculus",
        "chicken": "Gallus gallus",
    }
    from omero_search_engine.api.v1.resources.resource_analyser import (
        get_resource_attributes,
    )

    names = get_resource_attributes(res_table)
    if not names or len(names) == 0:
        search_omero_app.logger.info(
            "Could not check\
                                      filters %s"
            % str(filters)
        )
        return

    search_omero_app.logger.info(str(filters))
    if filters[0]:
        for filter in filters[0]:
            if not case_sensitive:
                check_single_filter(res_table, filter, names, organism_converter)
    if filters[1]:
        for filters_ in filters[1]:
            if isinstance(filters_, list):
                for filter in filters_:
                    if not case_sensitive:
                        check_single_filter(
                            res_table, filter, names, organism_converter
                        )


def search_index_scrol(index_name, query):
    results = []
    es = search_omero_app.config.get("es_connector")
    try:
        res = helpers.scan(client=es, scroll="1m", query=query, index=index_name)
    except Exception as ex:
        search_omero_app.logger.info(str(ex))
        return results

    search_omero_app.logger.info("Results: %s" % res)
    counter = 0
    for i in res:
        counter += 1
        results.append(i)
    search_omero_app.logger.info("Total =%s" % counter)
    return results


def get_bookmark(pagination_dict):
    """
    get book mark from the pagination section
    if the the request does not contain bookmark
    """
    bookmark = None
    if pagination_dict:
        next_page = pagination_dict["next_page"]
        bookmark = None
        for page_rcd in pagination_dict["page_records"]:
            if page_rcd["page"] == next_page:
                bookmark = page_rcd["bookmark"]
                break
    return bookmark


def get_pagination(total_pages, next_bookmark, pagination_dict):
    """
    This keeps track of pages, it can be used to track and lood pages (next by default)

    {
       "current_page":4,
       "next_page":5,
       "page_records":[
          {
             "bookmark":[
                304586
             ],
             "page":2
          },
          {
             "bookmark":[
                643303
             ],
             "page":3
          },
          {
             "bookmark":[
                1362671
             ],
             "page":4
          },
          {
             "bookmark":[
                1459210
             ],
             "page":5
          }
       ],
       "total_pages":13
        }
    """
    if not pagination_dict:
        pagination_dict = {}
        pagination_dict["total_pages"] = total_pages
        page_rcds = []
        pagination_dict["page_records"] = page_rcds
        pagination_dict["current_page"] = 1
        if total_pages > 1:
            pagination_dict["next_page"] = 2
        else:
            pagination_dict["next_page"] = None
        page_rcds.append({"page": 2, "bookmark": next_bookmark})
        return pagination_dict
    pagination_dict["current_page"] = pagination_dict["next_page"]
    if pagination_dict["current_page"] == total_pages:
        pagination_dict["next_page"] = None
        return pagination_dict
    pagination_dict["next_page"] = pagination_dict["next_page"] + 1
    if not get_bookmark(pagination_dict):
        next_page_record = {
            "page": pagination_dict["current_page"] + 1,
            "bookmark": next_bookmark,
        }
        page_records = pagination_dict.get("page_records")
        page_records.append(next_page_record)
    return pagination_dict


def search_index_using_search_after(
    e_index, query, bookmark_, pagination_dict, return_containers, ret_type=None
):
    returned_results = []
    if bookmark_ and not pagination_dict:
        add_paination = False
    else:
        add_paination = True

    es = search_omero_app.config.get("es_connector")
    if return_containers:
        res = es.search(index=e_index, body=query)
        if len(res["hits"]["hits"]) == 0:
            search_omero_app.logger.info("No result is found")
            return returned_results
        keys_counts = res["aggregations"]["key_count"]["buckets"]
        idrs = []
        for ek in keys_counts:
            idrs.append(ek["key"])
            res_res = get_studies_titles(ek["key"], ret_type)
            res_res["image count"] = ek["doc_count"]
            returned_results.append(res_res)

        return returned_results
    page_size = search_omero_app.config.get("PAGE_SIZE")
    res = es.count(index=e_index, body=query)
    size = res["count"]
    search_omero_app.logger.info("Total: %s" % size)
    query["size"] = page_size
    if size % page_size == 0:
        add_to_page = 0
    else:
        add_to_page = 1
    no_of_pages = (int)(size / page_size) + add_to_page
    search_omero_app.logger.info("No of pages: %s" % no_of_pages)
    query["sort"] = [{"id": "asc"}]
    if not bookmark_ and pagination_dict:
        bookmark_ = get_bookmark(pagination_dict)
    if not bookmark_:
        result = es.search(index=e_index, body=query)
        if len(result["hits"]["hits"]) == 0:
            search_omero_app.logger.info("No result is found")
            return returned_results
        bookmark = [result["hits"]["hits"][-1]["sort"][0]]
        search_omero_app.logger.info("bookmark: %s" % bookmark)
        for hit in result["hits"]["hits"]:
            # print (hit)
            returned_results.append(hit["_source"])
    else:
        search_omero_app.logger.info(bookmark_)
        query["search_after"] = bookmark_
        res = es.search(index=e_index, body=query)
        for el in res["hits"]["hits"]:
            returned_results.append(el["_source"])
        if len(res["hits"]["hits"]) == 0:
            search_omero_app.logger.info("No result is found")
            return returned_results
        bookmark = [res["hits"]["hits"][-1]["sort"][0]]
    results_dict = {
        "results": returned_results,
        "total_pages": no_of_pages,
        "bookmark": bookmark,
        "size": size,
    }
    if add_paination:
        pagination_dict = get_pagination(no_of_pages, bookmark, pagination_dict)
        results_dict["pagination"] = pagination_dict
    return results_dict


def handle_query(table_, query):
    pass


def search_resource_annotation_return_conatines_only(
    table_, query, raw_elasticsearch_query=None, page=None, bookmark=None
):
    pass


def search_resource_annotation(
    table_,
    query,
    raw_elasticsearch_query=None,
    bookmark=None,
    pagination_dict=None,
    return_containers=False,
):
    """
    @table_: the resource table, e.g. image. project, etc.
    @query: the a dict contains the three filters (or, and and  not) items
    @raw_elasticsearch_query: raw query sending directly to elasticsearch
    """
    try:
        res_index = resource_elasticsearchindex.get(table_)
        if not res_index:
            return build_error_message(
                "{table_} is not a valid resurce".format(table_=table_)
            )
        query_details = query.get("query_details")

        start_time = time.time()
        if not raw_elasticsearch_query:
            query_details = query.get("query_details")
            main_attributes = query.get("main_attributes")
            if not query_details and main_attributes and len(main_attributes) > 0:
                pass

            elif (
                not query
                or len(query) == 0
                or not query_details
                or len(query_details) == 0
                or isinstance(query_details, str)
            ):
                print("Error ")
                return build_error_message(
                    "{query} is not a valid query".format(query=query)
                )
            and_filters = query_details.get("and_filters")
            or_filters = query_details.get("or_filters")
            case_sensitive = query_details.get("case_sensitive")
            # check and fid if possible names and values inside
            # filters conditions
            check_filters(table_, [and_filters, or_filters], case_sensitive)
            query_string = elasticsearch_query_builder(
                and_filters, or_filters, case_sensitive, main_attributes
            )
            # query_string has to be string, if it is a dict,
            # something went wrong and the message inside the dict
            # which will be returned to the sender:
            if isinstance(query_string, dict):
                return query_string

            search_omero_app.logger.info("Query %s" % query_string)
            query = json.loads(query_string)
            raw_query_to_send_back = json.loads(query_string)
        else:
            query = raw_elasticsearch_query
            raw_query_to_send_back = copy.copy(raw_elasticsearch_query)
        if return_containers:
            # code to return the containers only
            # It will call the projects container first then
            # search within screens
            query["aggs"] = json.loads(
                count_attr_template.substitute(field="project_name.keyvalue")
            )
            query["_source"] = {"includes": [""]}
            res = search_index_using_search_after(
                res_index,
                query,
                bookmark,
                pagination_dict,
                return_containers,
                "project",
            )
            query["aggs"] = json.loads(
                count_attr_template.substitute(field="screen_name.keyvalue")
            )

            res_2 = search_index_using_search_after(
                res_index, query, bookmark, pagination_dict, return_containers, "screen"
            )
            # Combines the containers results
            studies = res + res_2
            res = {"results": studies}
        else:
            res = search_index_using_search_after(
                res_index, query, bookmark, pagination_dict, return_containers
            )
        notice = ""
        end_time = time.time()
        query_time = "%.2f" % (end_time - start_time)
        return {
            "results": res,
            "query_details": query_details,
            "resource": table_,
            "server_query_time": query_time,
            "raw_elasticsearch_query": raw_query_to_send_back,
            "notice": notice,
        }
    except Exception as e:
        search_omero_app.logger.info("Query %s" % str(query))
        search_omero_app.logger.info("==>>>Error: %s" % str(e))
        return build_error_message(
            "Something went wrong, please check your query and try again later."
        )


def get_studies_titles(idr_name, resource):
    """
    use the res_raw_query to return the study title (publication and study)
    """
    study_title = {}
    res_index = resource_elasticsearchindex.get(resource)
    resource_query = json.loads(res_raw_query.substitute(idr=idr_name))
    resourse_res = search_index_using_search_after(
        res_index, resource_query, None, None, None
    )
    for item_ in resourse_res["results"]:
        study_title["id"] = item_.get("id")
        study_title["name"] = item_.get("name")
        study_title["type"] = resource
        study_title["description"] = item_.get("description")
        for value in item_.get("key_values"):
            if value.get("name"):
                value["key"] = value["name"]
                del value["name"]
        study_title["key_values"] = item_.get("key_values")
    return study_title


def get_filter_list(filter):
    import copy

    new_or_filter = []
    f1 = copy.deepcopy(filter)
    f1["resource"] = "project"
    new_or_filter.append(f1)
    f2 = copy.deepcopy(filter)
    f2["resource"] = "screen"
    new_or_filter.append(f2)
    return new_or_filter


def adjust_query_for_container(query):
    query_details = query.get("query_details")
    new_or_filters = []
    to_delete_and_filter = []
    to_delete_or_filter = []
    if query_details:
        and_filters = query_details.get("and_filters")
        if and_filters:
            for filter in and_filters:
                if filter.get("resource") == "container":
                    new_or_filters.append(get_filter_list(filter))
                    to_delete_and_filter.append(filter)

        or_filters = query_details.get("or_filters")
        if or_filters:
            for filter in or_filters:
                if isinstance(filter, list):
                    for filter_ in filter:
                        if filter_.get("resource") == "container":
                            new_or_filters.append(get_filter_list(filter_))
                            to_delete_or_filter.append(filter_)
                else:
                    if filter.get("resource") == "container":
                        new_or_filters.append(get_filter_list(filter))
                        to_delete_or_filter.append(filter)
        for filter in to_delete_or_filter:
            if filter in or_filters:
                or_filters.remove(filter)
            else:
                for _filter in or_filters:
                    if isinstance(_filter, list):
                        if filter in _filter:
                            _filter.remove(filter)

        for filter in to_delete_and_filter:
            and_filters.remove(filter)

        for filter in new_or_filters:
            or_filters.append(filter)
