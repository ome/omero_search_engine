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
import datetime
import logging
import os
import sys
import json
from elasticsearch import helpers
import time
from omero_search_engine import search_omero_app
from string import Template
from app_data.data_attrs import annotation_resource_link
from flask import  Response

contain_list = ["contains", "not_contains"]
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

main_attribute_query_in_template = Template(
    """{"bool":{"must":{"terms":{"$attribute.keyvalue": $value }}}}"""
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

# in operator
case_insensitive_must_in_value_condition_template = Template(
    """
{"terms": {"key_values.value.keyvaluenormalize":$value}}"""
)

case_sensitive_must_value_condition_template = Template(
    """
{"match": {"key_values.value.keyvalue":"$value"}}"""
)

nested_query_template_must_must_not = Template(
    """
{"nested": {"path": "key_values",
"query":{"bool": {"must":[$must_part], "must_not":[$must_not_part]}}}}"""
)

# in opeartor
case_sensitive_must_in_value_condition_template = Template(
    """
{"terms": {"key_values.value.keyvalue":$value}}"""
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
{"wildcard": {"key_values.value.keyvaluenormalize":"$wild_card_value" }}"""
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

operators_required_list_data_type = ["in", "not_in"]


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
                        if attribute["operator"].strip() == "in":
                            # it is assuming that in operator value is a list
                            main_dd = main_attribute_query_in_template.substitute(
                                attribute=attribute["name"].strip(),
                                value=json.dumps(attribute["value"]),
                            )
                        elif (
                            attribute["name"].endswith("_id")
                            or attribute["name"] == "id"
                        ):
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
                        if (
                            attribute["operator"].strip() == "equals"
                            or attribute["operator"].strip() == "in"
                        ):
                            nested_must_part.append(main_dd)
                        elif attribute["operator"].strip() == "not_equals":
                            nested_must_not_part.append(main_dd)

                else:
                    attribute = clause
                    if attribute["operator"].strip() == "in":
                        # it is assuming that in operator value is a list
                        main_dd = main_attribute_query_in_template.substitute(
                            attribute=attribute["name"].strip(),
                            value=json.dumps(attribute["value"]),
                        )
                    elif attribute["name"].endswith("_id") or attribute["name"] == "id":
                        main_dd = main_attribute_query_template_id.substitute(
                            attribute=attribute["name"].strip(),
                            value=str(attribute["value"]).strip(),
                        )
                    else:
                        main_dd = main_attribute_query_template.substitute(
                            attribute=attribute["name"].strip(),
                            value=str(attribute["value"]).strip(),
                        )
                    if (
                        attribute["operator"].strip() == "equals"
                        or attribute["operator"].strip() == "in"
                    ):
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
                        if (
                            attribute["name"].endswith("_id")
                            or attribute["name"] == "id"
                        ):
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
                    if attribute["name"].endswith("_id") or attribute["name"] == "id":
                        main_dd = main_attribute_query_template_id.substitute(
                            attribute=attribute["name"].strip(),
                            value=str(attribute["value"]).strip(),
                        )

                    else:
                        main_dd = main_attribute_query_template.substitute(
                            attribute=attribute["name"].strip(),
                            value=str(attribute["value"]).strip(),
                        )
                    sh.append(main_dd)

                    # if attribute["operator"].strip() == "equals":
                    #    sh.append(main_dd)
                    # elif attribute["operator"].strip() == "not_equals":
                    #    sh.append(main_dd)

            # if len(should_part_list)>0:
            #    minimum_should_match=len(should_part_list)

    if and_filter and len(and_filter) > 0:
        for filter in and_filter:
            search_omero_app.logger.info("FILTER %s" % filter)
            try:
                key = filter.get("name")
                if key:
                    key = key.strip()
                # value = filter["value"].strip()

                operator = filter["operator"].strip()
                if operator in operators_required_list_data_type:
                    if isinstance(filter["value"], list):
                        value_ = filter["value"]
                    else:
                        # in case of providing it with single query, the values should
                        # be provided as a string separated the array items by ','
                        value_ = filter["value"].split(",")
                    value = [val.strip() for val in value_]
                    value = json.dumps(value)

                else:
                    value = filter["value"].strip()

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
                    if key:
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
                    if key:
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

            if operator == "in":
                if case_sensitive:
                    _nested_must_part.append(
                        case_sensitive_must_in_value_condition_template.substitute(  # noqa
                            value=value
                        )
                    )
                    _nested_must_part.append(
                        case_sensitive_must_name_condition_template.substitute(name=key)
                    )  # noqa

                else:
                    _nested_must_part.append(
                        case_insensitive_must_in_value_condition_template.substitute(  # noqa
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

            if operator == "not_in":
                if case_sensitive:
                    if key:
                        nested_must_part.append(
                            nested_query_template_must_must_not.substitute(
                                must_not_part=case_sensitive_must_in_value_condition_template.substitute(  # noqa
                                    value=value
                                ),
                                must_part=case_sensitive_must_name_condition_template.substitute(  # noqa
                                    name=key
                                ),
                            )
                        )
                    else:
                        nested_must_part.append(
                            nested_query_template_must_must_not.substitute(
                                must_not_part=case_sensitive_must_in_value_condition_template.substitute(  # noqa
                                    value=value
                                ),
                            )
                        )

                else:
                    if key:
                        nested_must_part.append(
                            nested_query_template_must_must_not.substitute(
                                must_not_part=case_insensitive_must_in_value_condition_template.substitute(  # noqa
                                    value=value
                                ),
                                must_part=case_insensitive_must_name_condition_template.substitute(  # noqa
                                    name=key
                                ),
                            )
                        )
                    else:
                        nested_must_part.append(
                            nested_query_template_must_must_not.substitute(
                                must_not_part=case_insensitive_must_in_value_condition_template.substitute(  # noqa
                                    value=value
                                ),
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
                    if key:
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
                    if key:
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
                        if key:
                            nested_must_part.append(
                                nested_keyvalue_pair_query_template.substitute(
                                    nested=case_sensitive_wildcard_value_condition_template.substitute(  # noqa
                                        wild_card_value=value
                                    ),
                                    must_part=case_sensitive_must_name_condition_template.substitute(  # noqa
                                        name=key
                                    ),
                                )
                            )
                        else:
                            nested_must_not_part.append(
                                nested_keyvalue_pair_query_template.substitute(
                                    nested=case_sensitive_wildcard_value_condition_template.substitute(  # noqa
                                        wild_card_value=value
                                    ),
                                )
                            )

                    else:
                        if key:
                            nested_must_part.append(
                                nested_query_template_must_must_not.substitute(
                                    must_not_part=case_insensitive_wildcard_value_condition_template.substitute(  # noqa
                                        wild_card_value=value
                                    ),
                                    must_part=case_insensitive_must_name_condition_template.substitute(  # noqa
                                        name=key
                                    ),
                                )
                            )
                        else:
                            nested_must_part.append(
                                nested_query_template_must_must_not.substitute(
                                    must_not_part=case_insensitive_wildcard_value_condition_template.substitute(  # noqa
                                        wild_card_value=value
                                    ),
                                    must_part=[],
                                )
                            )
                else:
                    if case_sensitive:
                        if key:
                            nested_must_part.append(
                                nested_query_template_must_must_not.substitute(
                                    must_not_part=case_sensitive_must_value_condition_template.substitute(  # noqa
                                        value=value
                                    ),
                                    must_part=case_sensitive_must_name_condition_template.substitute(  # noqa
                                        name=key
                                    ),
                                )
                            )
                        else:
                            nested_must_part.append(
                                nested_query_template_must_must_not.substitute(
                                    must_not_part=case_sensitive_wildcard_value_condition_template.substitute(  # noqa
                                        wild_card_value=value
                                    ),
                                    must_part="",
                                )
                            )
                    else:
                        if key:
                            nested_must_part.append(
                                nested_query_template_must_must_not.substitute(
                                    must_not_part=case_insensitive_must_value_condition_template.substitute(  # noqa
                                        value=value
                                    ),
                                    must_part=case_insensitive_must_name_condition_template.substitute(  # noqa
                                        name=key
                                    ),
                                )
                            )
                        else:

                            nested_must_part.append(
                                nested_query_template_must_must_not.substitute(
                                    must_not_part=case_insensitive_wildcard_value_condition_template.substitute(  # noqa
                                        wild_card_value=value
                                    ),
                                    must_part="",
                                )
                            )

            elif operator in ["lt", "lte", "gt", "gte"]:
                # nested_must_part.append(nested_keyvalue_pair_query_template.substitute(nested=must_name_condition_template.substitute(name=key))) # noqa
                if case_sensitive:
                    if key:
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
                    if key:
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
                    key = or_filter.get("name")
                    if key:
                        key = key.strip()
                    value = or_filter["value"].strip()
                    operator = or_filter["operator"].strip()
                except Exception:
                    return build_error_message(
                        "Each Filter needs to have,\
                        name, value and operator keywords."
                    )

                if key and key not in added_keys:
                    added_keys.append(key)

                if operator == "equals":
                    if case_sensitive:
                        should_values.append(
                            case_sensitive_must_value_condition_template.substitute(  # noqa
                                value=value
                            )
                        )
                        if key:
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
                        if key:
                            should_values.append(
                                case_insensitive_must_name_condition_template.substitute(  # noqa
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
                        if key:
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
                        if key:
                            should_values.append(
                                case_insensitive_must_name_condition_template.substitute(  # noqa
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
                            if key:
                                shoud_not_value.append(
                                    case_sensitive_must_name_condition_template.substitute(  # noqa
                                        name=key
                                    )
                                )
                        else:
                            shoud_not_value.append(
                                case_insensitive_wildcard_value_condition_template.substitute(  # noqa
                                    wild_card_value=value
                                )
                            )
                            if key:
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
                            if key:
                                shoud_not_value.append(
                                    case_sensitive_must_name_condition_template.substitute(  # noqa
                                        name=key
                                    )
                                )
                        else:
                            shoud_not_value.append(
                                case_insensitive_must_value_condition_template.substitute(  # noqa
                                    value=value
                                )
                            )
                            if key:
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
                        if key:
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
                    if key:
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
    key = filter.get("name")
    value = filter["value"]
    operator = filter["operator"]
    if operator not in contain_list:
        if key:
            for names_ in names:
                key_ = [name for name in names_ if name.casefold() == key.casefold()]
        else:
            key_ = []
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
    e_index,
    query,
    bookmark_,
    pagination_dict,
    return_containers,
    data_source=None,
    ret_type=None,
    random_results=0,
) -> object:
    returned_results = []
    if bookmark_ and not pagination_dict:
        add_pagination = False
    else:
        add_pagination = True
    if not data_source:
        data_source = get_data_sources()
    es = search_omero_app.config.get("es_connector")
    if return_containers:
        #####
        for data_s in data_source:
            query2 = copy.deepcopy(query)
            main_dd = main_attribute_query_in_template.substitute(
                attribute="data_source",
                value=json.dumps([data_s]),
            )
            # query["query"]["bool"]["must"][0] = json.loads(main_dd)
            if "must" in query2["query"]["bool"]:
                query2["query"]["bool"]["must"].append(json.loads(main_dd))
            else:
                query2["query"]["bool"]["must"] = [json.loads(main_dd)]
            res = es.search(index=e_index, body=query2)
            if len(res["hits"]["hits"]) == 0:
                search_omero_app.logger.info("No result found")
                continue
            keys_counts = res["aggregations"]["key_count"]["buckets"]
            idrs = []
            for ek in keys_counts:
                idrs.append(ek["key"])
                res_res = get_studies_titles(ek["key"], ret_type, data_s)
                res_res["image count"] = ek["doc_count"]
                if data_source:
                    res_res["data_source"] = data_s
                returned_results.append(res_res)

        return returned_results
    page_size = search_omero_app.config.get("PAGE_SIZE")
    res = es.count(index=e_index, body=query)
    size = res["count"]
    search_omero_app.logger.info("Total: %s" % size)
    if random_results > 0:
        query["sort"] = [
            {
                "_script": {
                    "type": "number",
                    "script": {"source": "Math.random()"},
                    "order": "asc",
                }
            }
        ]
        query["explain"] = True
        query["size"] = random_results
    else:
        query["size"] = page_size

        if size % page_size == 0:
            add_to_page = 0
        else:
            add_to_page = 1
        no_of_pages = (int)(size / page_size) + add_to_page
        search_omero_app.logger.info("Number of pages: %s" % no_of_pages)
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
    if random_results == 0:
        results_dict = {
            "results": returned_results,
            "total_pages": no_of_pages,
            "bookmark": bookmark,
            "size": size,
        }
        if add_pagination:
            pagination_dict = get_pagination(no_of_pages, bookmark, pagination_dict)
            results_dict["pagination"] = pagination_dict

    else:
        results_dict = {
            "results": returned_results,
            "bookmark": bookmark,
            "size": size,
        }
    return results_dict


def handle_query(table_, query):
    pass


def search_resource_annotation_return_containers_only(
    query,
    data_source,
    return_columns,
    return_containers,
):
    from omero_search_engine.api.v1.resources.query_handler import (
        determine_search_results_,
    )

    all_data_sources = get_data_sources()
    if not data_source:
        data_sources = all_data_sources
    else:
        data_sources = data_source.split(",")
        for data_s in data_sources:
            if data_s and data_s.strip().lower() not in all_data_sources:
                return "'%s' is not a data source" % data_s

    results = {}
    for data_s in data_sources:
        res = determine_search_results_(
            query, data_s, return_columns, return_containers
        )

        if type(res) is dict and len(res) > 0:
            if len(res) == 1 and res.get("Error"):
                logging.info(
                    "Data source %s Error: %s" % (data_s, results.get("Error"))
                )
                continue
            elif len(results) == 0:
                results = res
            else:
                search_omero_app.logger.info("Adding RESULTS FOUND FOR %s" % data_s)
                results["results"]["results"] = (
                    results["results"]["results"] + res["results"]["results"]
                )
        else:
            search_omero_app.logger.info(
                "No results found from the data source: %s" % data_s
            )

    return results


def search_resource_annotation(
    table_,
    query,
    raw_elasticsearch_query=None,
    bookmark=None,
    pagination_dict=None,
    return_containers=False,
    data_source=None,
    random_results=0,
):
    """
    @table_: the resource table, e.g. image. project, etc.
    @query: the dict contains the three filters (or, and and  not) items
    @raw_elasticsearch_query: raw query sending directly to elasticsearch
    """
    # try:
    res_index = resource_elasticsearchindex.get(table_)
    if not res_index:
        return build_error_message(
            "{table_} is not a valid resource".format(table_=table_)
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
            logging.info("Error ")
            return build_error_message(
                "{query} is not a valid query".format(query=query)
            )
        if data_source and data_source != "all":
            data_sources = get_data_sources()
            if type(data_source) is str:
                data_source = [itm.strip() for itm in data_source.split(",")]
            for data_s in data_source:
                if data_s and data_s.strip().lower() not in data_sources:
                    return "'%s' is not a data source" % data_s
            clause = {}
            clause["name"] = "data_source"
            clause["value"] = data_source
            clause["operator"] = "in"
            if main_attributes and len(main_attributes) > 0:
                if main_attributes.get("and_main_attributes"):
                    main_attributes.get("and_main_attributes").append(clause)
                else:
                    main_attributes["and_main_attributes"] = [clause]
            else:
                main_attributes = {}
                main_attributes["and_main_attributes"] = [clause]

        and_filters = query_details.get("and_filters")
        or_filters = query_details.get("or_filters")
        case_sensitive = query_details.get("case_sensitive")
        query_string = elasticsearch_query_builder(
            and_filters, or_filters, case_sensitive, main_attributes
        )
        # query_string has to be a string, if it is a dict,
        # something went wrong and the message inside the dict
        # will be returned to the sender:
        if isinstance(query_string, dict):
            return query_string

        # search_omero_app.logger.info("Query %s" % query_string)

        from ast import literal_eval

        try:
            query = literal_eval(query_string)
            raw_query_to_send_back = literal_eval(query_string)
        except Exception as ex:
            raise Exception("Failed to load the query, error: %s" % str(ex))
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
            data_source=data_source,
            ret_type="project",
            random_results=random_results,
        )
        query["aggs"] = json.loads(
            count_attr_template.substitute(field="screen_name.keyvalue")
        )
        res_2 = search_index_using_search_after(
            res_index,
            query,
            bookmark,
            pagination_dict,
            return_containers,
            data_source=data_source,
            ret_type="screen",
        )
        # Combines the containers results
        studies = res + res_2
        res = {"results": studies}
    else:
        res = search_index_using_search_after(
            res_index,
            query,
            bookmark,
            pagination_dict,
            return_containers,
            data_source=data_source,
            random_results=random_results,
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


def get_studies_titles(idr_name, resource, data_source=None):
    """
    use the res_raw_query to return the study title (publication and study)
    """
    study_title = {}
    res_index = resource_elasticsearchindex.get(resource)
    resourse_res = []
    try:
        resource_query = json.loads(res_raw_query.substitute(idr=idr_name))
        resourse_res = search_index_using_search_after(
            res_index, resource_query, None, None, None, data_source
        )
    except Exception as ex:
        search_omero_app.logger.info(
            "Error for name %s and datasource %s, error message: %s "
            % (idr_name, data_source, str(ex))
        )
    if len(resourse_res) > 0:
        for item_ in resourse_res["results"]:
            study_title["id"] = item_.get("id")
            study_title["name"] = item_.get("name")
            study_title["type"] = resource
            for value in item_.get("key_values"):
                if value.get("name"):
                    value["key"] = value["name"]
                    del value["name"]
            study_title["key_values"] = item_.get("key_values")
    return study_title


def get_filter_list(filter, org_type):
    import copy

    new_or_filter = []
    f1 = copy.deepcopy(filter)
    f1["resource"] = "project"
    f1["org_type"] = org_type
    new_or_filter.append(f1)
    f2 = copy.deepcopy(filter)
    f2["resource"] = "screen"
    f2["org_type"] = org_type
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
                    new_or_filters.append(get_filter_list(filter, "and"))
                    to_delete_and_filter.append(filter)

        or_filters = query_details.get("or_filters")
        if or_filters:
            for filter in or_filters:
                if isinstance(filter, list):
                    for filter_ in filter:
                        if filter_.get("resource") == "container":
                            new_or_filters.append(get_filter_list(filter_, "or"))
                            to_delete_or_filter.append(filter_)
                else:
                    if filter.get("resource") == "container":
                        new_or_filters.append(get_filter_list(filter, "or"))
                        to_delete_or_filter.append(filter)
        else:
            or_filters = []
            query_details["or_filters"] = or_filters
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
        tt = []
        for o_f in or_filters:
            if len(o_f) == 0:
                tt.append(o_f)
        for f in tt:
            or_filters.remove(f)


def get_data_sources():
    data_sources = []
    for data_source in search_omero_app.config.database_connectors.keys():
        data_sources.append(data_source)
    for data_source in search_omero_app.config.get("FILES").keys():
        data_sources.append(data_source)
    return data_sources


def check_empty_string(string_to_check):
    if string_to_check:
        string_to_check = string_to_check.strip()
    return string_to_check


def get_all_index_data(res_table, data_source):
    query_return_all_data = {
        "query_details": {"and_filters": [], "or_filters": [], "case_sensitive": False}
    }
    res = search_resource_annotation(
        res_table,
        query_return_all_data,
        return_containers=False,
        data_source=data_source,
    )
    return res


##################
def get_number_image_inside_container(resource, res_id, data_source):
    and_filters = []
    main_attributes = {
        "and_main_attributes": [
            {
                "name": "%s_id" % resource,
                "value": res_id,
                "operator": "equals",
                "resource": "image",
            },
            {
                "name": "data_source",
                "value": data_source,
                "operator": "equals",
                "resource": "image",
            },
        ]
    }
    or_filters = []
    query = {"and_filters": and_filters, "or_filters": or_filters}

    query_data = {
        "query_details": query,
        "main_attributes": main_attributes,
    }

    returned_results = search_resource_annotation("image", query_data)
    if returned_results.get("results"):
        if returned_results.get("results").get("size"):
            searchengine_results = returned_results["results"]["size"]
    else:
        searchengine_results = 0

    return searchengine_results


def get_working_data_source(requested_datasource):
    data_sources = get_data_sources()
    default_datasource = search_omero_app.config.get("DEFAULT_DATASOURCE")
    requested_datasource = check_empty_string(requested_datasource)
    if requested_datasource:
        requested_datasource = [
            item.strip() for item in requested_datasource.split(",")
        ]
        return ",".join(requested_datasource)
    elif default_datasource:
        return default_datasource
    else:
        return ",".join(data_sources)


def delete_data_source_cache(data_source):
    es = search_omero_app.config.get("es_connector")
    search_omero_app.logger.info("delete cache for data source %s" % data_source)
    delete_cache = delete_cache_query.substitute(data_source=data_source)
    es_index = "key_value_buckets_information"
    es_index_2 = "key_values_resource_cached"
    try:
        res_1 = es.delete_by_query(
            index=es_index, body=json.loads(delete_cache), request_timeout=1000
        )
        search_omero_app.logger.info("delete cache result 1 %s" % res_1)
        res_2 = es.delete_by_query(
            index=es_index_2, body=json.loads(delete_cache), request_timeout=1000
        )
        search_omero_app.logger.info("delete cache result 2 %s" % res_2)
    # Trigger caching for  the data source
    except Exception as e:
        search_omero_app.logger.info(
            "Error deleting cache for data source %s, error message is %s"
            % (data_source, str(e))
        )


def get_number_of_images_inside_container(resource_table, data_source, id):
    name_result = get_all_index_data(resource_table, data_source)
    no_images_co = 0
    for res in name_result["results"]["results"]:
        if res.get("id") == int(id):
            no_images_co = get_number_image_inside_container(
                resource_table, id, data_source
            )
            break
    return no_images_co


def update_data_source_cache(data_source, res=None, delete_current_cache=True):
    from omero_search_engine.cache_functions.elasticsearch.transform_data import (
        save_key_value_buckets,
    )

    delete_data_source_cache(data_source)
    search_omero_app.logger.info("Trigger caching for data source %s" % data_source)
    save_key_value_buckets(res, data_source, False, False)


def delete_container(ids, resource, data_source, update_cache, synchronous_run=False):
    """
    Delete a container (project or screen) from the searchengine
     Also delete all images inside it and cache the data
     delete cache and create it again
     the data source caching should be re-created
    """
    # "request_cache": false,
    st = datetime.datetime.now()

    from omero_search_engine.api.v1.resources.resource_analyser import (
        get_containers_no_images,
    )

    es = search_omero_app.config.get("es_connector")
    ids = ids.split(",")
    for id in ids:
        no_images = get_number_of_images_inside_container(resource, data_source, id)
        if no_images == 0:
            search_omero_app.logger.info(
                "The requested %s with ID=%s does not correspond to any existing one."
                % (resource, id)
            )
            return
        elif no_images > 740000 and synchronous_run:
            # This number has been approximately estimated through trial and error.
            search_omero_app.logger.info(
                "Due to the high number of images in the %s with ID=%s, "
                "an asynchronous delete operation is highly advised. "
                "\nPlease rerun with asynchronous deletion enable (-s False)."
                % (resource, id)
            )
            return

        sub_containers = get_containers_no_images(
            container_id=id, data_source=data_source, resource=resource
        )
        if (
            type(sub_containers) is not str
            and sub_containers.get("results")
            and sub_containers.get("results").get("results")
        ):
            counter = 0
            idss = {}
            for res in sub_containers["results"]["results"]:
                counter += 1
                if idss.get(res["resource"]):
                    idss[res["resource"]].append(str(res["id"]))
                else:
                    idss[res["resource"]] = [str(res["id"])]

            for resou, ids in idss.items():
                if not resource_elasticsearchindex.get(resou):
                    continue

                sub_container_delet_query = delete_container_query.substitute(
                    attribute="id", id=(",").join(ids), data_source=data_source
                )
                # check
                # res__2 = delete_container_res = es.delete_by_query(
                res__2 = es.delete_by_query(
                    index=resource_elasticsearchindex[resou],
                    body=json.loads(sub_container_delet_query),
                    request_cache=False,
                    wait_for_completion=synchronous_run,
                    error_trace=True,
                )
                search_omero_app.logger.info(
                    "%s/%s, delete results is %s"
                    % (counter, len(sub_containers["results"]["results"]), res__2)
                )
        attribute = "%s_id" % resource
        image_delet_query = delete_container_query.substitute(
            attribute=attribute, id=id, data_source=data_source
        )

        container_delet_query = delete_container_query.substitute(
            attribute="id", id=int(id), data_source=data_source
        )

        # Delete container
        search_omero_app.logger.info(
            "Delete %s with Id %s from data source: %s" % (resource, id, data_source)
        )
        delete_container_res = es.delete_by_query(
            index=resource_elasticsearchindex[resource],
            body=json.loads(container_delet_query),
            request_cache=False,
            wait_for_completion=synchronous_run,
            error_trace=True,
        )
        search_omero_app.logger.info("Delete results: %s" % delete_container_res)

        # Delete images inside the container
        search_omero_app.logger.info("Delete images inside the  %s" % resource)
        delete_image_res = es.delete_by_query(
            index=resource_elasticsearchindex["image"],
            body=json.loads(image_delet_query),
            request_cache=False,
            wait_for_completion=synchronous_run,
            error_trace=True,
        )
        search_omero_app.logger.info("Delete results: %s" % delete_image_res)

    if update_cache and synchronous_run:
        # update the cache for the data source
        update_data_source_cache(data_source)
    else:
        delete_data_source_cache(data_source)
    en = datetime.datetime.now()
    search_omero_app.logger.info("Start at: %s" % st)
    search_omero_app.logger.info("Ends at: %s" % en)


def delete_data_source_contents(data_source):
    found = False
    if not data_source:
        search_omero_app.logger.info("Data source is not provided")
        return found
    data_sources = get_data_sources()
    for d_s in data_sources:
        if d_s.lower() == data_source.lower():
            found = True
            break
    if not found:
        search_omero_app.logger.info("Data source %s is not found" % data_source)
        return found

    st = datetime.datetime.now()
    resources_index = ["image", "project", "screen", "well", "plate"]
    query = delete_datasource_query.substitute(data_source=data_source)
    es = search_omero_app.config.get("es_connector")
    for res in resources_index:
        #  Not enough active copies to meet shard count of
        try:
            search_omero_app.logger.info("Please wait while deleting  %s" % res)
            delete_sub_res = es.delete_by_query(
                index=resource_elasticsearchindex[res],
                body=json.loads(query),
                refresh=True,
                wait_for_active_shards="all",
                wait_for_completion=False,
                slices="auto",
                scroll="10m",
                # requests_per_second=-1,
            )
            search_omero_app.logger.info(
                "Delete results for %s is %s" % (res, delete_sub_res)
            )
            es.indices.refresh(index=resource_elasticsearchindex[res])
        except Exception as ex:
            search_omero_app.logger.info(
                "Error while deleting  %s, error is %s" % (res, ex)
            )

    # delete data source cache
    delete_cache = delete_cache_query.substitute(data_source=data_source)
    es_index = ["key_value_buckets_information", "key_values_resource_cached"]
    for e_inxex in es_index:
        try:
            search_omero_app.logger.info(
                "Deleting cache inside %s for data source %s" % (e_inxex, data_source)
            )
            res_1 = es.delete_by_query(
                index=e_inxex,
                body=json.loads(delete_cache),
                request_timeout=1000,
                refresh=True,
                wait_for_active_shards="all",
                wait_for_completion=False,
                slices="auto",
                scroll="10m",
            )
            es.indices.refresh(index=es_index)
            search_omero_app.logger.info("delete cache result 1 %s" % res_1)
        except Exception as ex:
            search_omero_app.logger.info(
                "Error while deleting cache inside  %s, error is %s" % (e_inxex, ex)
            )

    en = datetime.datetime.now()

    search_omero_app.logger.info("start time %s , end time %s" % (st, en))
    return found


def write_BBF(results, file_name=None, return_contents=False):
    import pandas as pd
    print("=====================================")
    print (type(results))
    print ("=====================================")

    to_ignore_list = {
        "project": [
            "dataset_id",
            "dataset_name",
            "doc_type",
            "experiment",
            "group_id",
            "image_size",
            "owner_id",
            "plate_id",
            "plate_name",
            "screen_name",
            "screen_id",
            "well_id",
            "wellsample_id",
        ],
        "screen": [
            "dataset_id",
            "dataset_name",
            "doc_type",
            "experiment",
            "group_id",
            "image_size",
            "owner_id",
            "dataset_name",
            "project_id",
            "project_name",
            "well_id",
            "wellsample_id",
        ],
    }
    col_converter = {"image_url": "File Path", "thumb_url": "Thumbnail"}
    lines = []
    for row_ in results:
        line = {}
        lines.append(line)
        print (row_)
        print ("========================")
        if row_.get("project_id"):
            resource="project"
        else:
            resource="screen"
        for name, item in row_.items():
            print (name)
            print ("###############################")
            if name in to_ignore_list[resource]:
                continue
            if name == "key_values" and len(item) > 0:
                for row in item:
                    line[row["name"]] = row["value"]
            else:
                if name in col_converter:
                    line[col_converter[name]] = item
                else:
                    line[name] = item

    df = pd.DataFrame(lines)
    if return_contents:
        return df.to_csv()
    df.to_csv(file_name)
    print(len(lines))


def create_bff_file_response(file_contents,resource):
    file_name = "bff"
    return Response(
        file_contents,
        mimetype="text/csv",
        headers={
            "Content-disposition": "attachment; filename=%s_%s.csv"
                                   % (file_name, resource)
        },
    )

delete_container_query = Template(
    """
{"query":{
      "bool":{"must":[{
               "bool":{
                  "must":{
                     "terms":{
                        "$attribute":[$id]}}}},{
               "bool":{
                  "must":{
                     "match":{
                        "data_source.keyvalue":"$data_source"
                     }}}}]}}}
"""
)

delete_cache_query = Template(
    """
{"query":{"bool":{"must":[{"bool":{
                  "must":{
                     "match":{
                        "data_source.keyvalue":"$data_source"
                     }}}}]}}}
"""
)

delete_datasource_query = Template(
    """
        {
   "query":{
      "bool":{
         "must":[
            {
               "bool":{
                  "must":{
                     "match":{
                        "data_source.keyvalue":"$data_source"
                     }}}}]}}}
"""
)
