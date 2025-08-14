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

from omero_search_engine import search_omero_app
from resource_analyser import return_containers_images, get_containers_no_images
import os
import json


def create_container_folder(parent_folder, container_name=None):
    if not os.path.isdir(parent_folder):
        os.mkdir(parent_folder)
    if container_name:
        folder = os.path.join(parent_folder, container_name)
        if not os.path.isdir(folder):
            os.makedirs(folder, exist_ok=True)
        return folder


def dump_data(target_folder, id, resource, over_write, bbf_format, data_source="idr"):
    from datetime import datetime
    from omero_search_engine.api.v1.resources.utils import get_working_data_source

    data_source = get_working_data_source(data_source)
    start_time = datetime.now()
    totalrecords = 0
    duplicated = []
    if not target_folder:
        target_folder = "/tmp"
    folders = {}
    found = False
    projects_folder = create_container_folder(target_folder, "projects")
    folders["project"] = projects_folder
    screens_folder = create_container_folder(target_folder, "screens")
    folders["screen"] = screens_folder
    containers = return_containers_images(data_source)
    for container in containers["results"]["results"]:
        if resource and id:
            if container["id"] == int(id) and container["type"] == resource:
                found = True
            else:
                continue
        print(container["type"], container["name"])

        sub_containers = get_containers_no_images(
            container["name"],
            container["id"],
            None,
            resource=container["type"],
            data_source=data_source,
        )
        container_type = container["type"]
        container_id = container["id"]
        container_name = container["name"]
        container_folder = create_container_folder(
            folders[container_type], container_name
        )
        #  create su-folcder,
        #  make it working folder
        #  save sub-container json file using file name
        for sub_container in sub_containers["results"]["results"]:
            print(sub_container)
            if bbf_format:
                file_name = os.path.join(
                    container_folder, "%s.csv" % sub_container["name"].replace("/", "_")
                )
            else:
                file_name = os.path.join(
                    container_folder,
                    "%s.json" % sub_container["name"].replace("/", "_"),
                )
            if not over_write and os.path.isfile(file_name):
                continue
            # else:
            query = {"and_filters": [], "or_filters": [[]]}
            main_attributes_query = {
                "and_main_attributes": [
                    {
                        "name": "%s_id" % container_type,
                        "value": container_id,
                        "operator": "equals",
                    },
                    {
                        "name": "%s_name" % sub_container["resource"],
                        "value": sub_container["name"],
                        "operator": "equals",
                    },
                    {"name": "data_source", "value": data_source, "operator": "equals"},
                ]
            }

            print(main_attributes_query)

            results = get_subcontainer_data(
                query, main_attributes_query, data_source, duplicated
            )
            print(len(results))
            if bbf_format:
                write_BBF(results, container_type, file_name)
            else:
                save_results_file(results, file_name)
            totalrecords += len(results)
        if found:
            break

    end_time = datetime.now()
    search_omero_app.logger.info("Elapsed time: : %s" % (end_time - start_time))
    search_omero_app.logger.info("Total images: %s" % totalrecords)


def get_bookmark(pagination_dict):
    next_page = pagination_dict["next_page"]
    for page_rcd in pagination_dict["page_records"]:
        if page_rcd["page"] == next_page:
            return page_rcd["bookmark"]


def get_subcontainer_data(query, main_attributes, data_source, duplicated):
    from utils import search_resource_annotation

    received_results_data = []
    query_data = {"query_details": query, "main_attributes": main_attributes}

    returned_results = search_resource_annotation(
        "image",
        query_data,
        raw_elasticsearch_query=None,
        bookmark=None,
        pagination_dict=None,
        return_containers=False,
        data_source=data_source,
    )

    if not returned_results.get("results") or len(returned_results["results"]) == 0:
        search_omero_app.logger.info("Your query returns no results")
        search_omero_app.logger.info(returned_results)

        return []

    search_omero_app.logger.info("Query results:")
    total_results = returned_results["results"]["size"]
    search_omero_app.logger.info("Total no of result records %s" % total_results)
    search_omero_app.logger.info(
        "Server query time: %s seconds" % returned_results["server_query_time"]
    )
    search_omero_app.logger.info(
        "Included results in the current page %s"
        % len(returned_results["results"]["results"])
    )

    for res in returned_results["results"]["results"]:
        received_results_data.append(res)

    received_results = len(returned_results["results"]["results"])
    # get the total number of pages
    total_pages = returned_results["results"]["total_pages"]
    pagination_dict = returned_results["results"].get("pagination")

    page = pagination_dict["current_page"]
    search_omero_app.logger.info(
        "page: %s, received results: %s"
        % (
            (str(page) + "/" + str(total_pages)),
            (str(received_results) + "/" + str(total_results)),
        )
    )
    bookmark = get_bookmark(pagination_dict)
    page = pagination_dict["next_page"]
    print(bookmark)
    ids = []
    while page:
        query_data = {
            "query_details": query,
            "main_attributes": main_attributes,
            "pagination": pagination_dict,
        }
        returned_results = search_resource_annotation(
            "image",
            query_data,
            raw_elasticsearch_query=None,
            bookmark=bookmark,
            pagination_dict=pagination_dict,
            return_containers=False,
            data_source=data_source,
        )
        # if returned_results.get("results"):
        pagination_dict = returned_results["results"].get("pagination")

        received_results = received_results + len(
            returned_results["results"]["results"]
        )
        for res in returned_results["results"]["results"]:
            if res["id"] in ids:
                duplicated.append(res["id"])
            ids.append(res["id"])
            received_results_data.append(res)
        if len(received_results_data) >= returned_results["results"]["size"]:
            break

        search_omero_app.logger.info(
            "bookmark: %s, page: %s, received results: %s"
            % (
                bookmark,
                (str(page) + "/" + str(total_pages)),
                (str(received_results) + "/" + str(total_results)),
            )
        )
        if pagination_dict:
            page = pagination_dict.get("next_page")
        else:
            break
        bookmark = get_bookmark(pagination_dict)

    search_omero_app.logger.info(
        "Total received results: %s" % len(received_results_data)
    )
    return received_results_data


def save_results_file(results, file_name="results.json"):
    with open(file_name, "w") as outfile:
        outfile.write(json.dumps(results, indent=4))


def write_BBF(results, resource, file_name):
    import pandas as pd

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
    count = 0
    for row_ in results:
        line = {}
        lines.append(line)
        count += 1
        for name, item in row_.items():
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
    df.to_csv(file_name)
    print(len(lines))
