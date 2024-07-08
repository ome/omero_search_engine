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
from elasticsearch import helpers
import pandas as pd
import numpy as np
import os
import uuid
from omero_search_engine.api.v1.resources.utils import resource_elasticsearchindex
from omero_search_engine.api.v1.resources.resource_analyser import (
    query_cashed_bucket,
    get_all_values_for_a_key,
)
from omero_search_engine.cache_functions.elasticsearch.elasticsearch_templates import (  # noqa
    image_template,
    non_image_template,
    key_value_buckets_info_template,
    key_values_resource_cache_template,
)
from omero_search_engine.validation.psql_templates import (
    query_images_in_project_id,
    query_images_screen_id,
)

from app_data.data_attrs import annotation_resource_link
from datetime import datetime
import multiprocessing
from functools import partial

import json


def create_index(es_index, template):
    es = search_omero_app.config.get("es_connector")
    try:
        response = es.indices.create(index=es_index, body=template)

        if "acknowledged" in response:
            if response["acknowledged"] is True:
                search_omero_app.logger.info(
                    "INDEX MAPPING SUCCESS FOR INDEX: %s" % response["index"]
                )
        # catch API error response
        elif "error" in response:
            error = response["error"]
            search_omero_app.logger.info("ERROR: %s" % error["root_cause"])
            search_omero_app.logger.info("TYPE: %s" % error["type"])
            return False
    except Exception as ex:
        search_omero_app.logger.info(
            "Error while creating index {es_index},\
             error message: {error}".format(
                es_index=es_index, error=str(ex)
            )
        )
        return False

    return True


def create_omero_indexes(resource):
    if resource != "all" and not resource_elasticsearchindex.get(resource):
        search_omero_app.logger.info(
            "No index template found for resource: %s" % resource
        )

    for resource_, es_index in resource_elasticsearchindex.items():
        if resource != "all" and resource_ != resource:
            continue
        if resource_ == "image":
            template = image_template
        else:
            template = non_image_template
        search_omero_app.logger.info(
            f"Creating index {es_index} for {resource_}".format(
                es_index=es_index, resource=resource_
            )
        )
        create_index(es_index, template)


def get_all_indexes():
    return [
        "project_keyvalue_pair_metadata",
        "screen_keyvalue_pair_metadata",
        "plate_keyvalue_pair_metadata",
        "well_keyvalue_pair_metadata",
        "image_keyvalue_pair_metadata",
        "key_value_buckets_information",
        "key_values_resource_cach",
    ]


def get_all_indexes_from_elasticsearch():
    es = search_omero_app.config.get("es_connector")
    all_indexes = es.indices.get("*")
    return all_indexes


def rename_index(old_index, new_index):
    es = search_omero_app.config.get("es_connector")
    response = es.indices.reindex(source=old_index, dest=new_index)
    if "acknowledged" in response:
        if response["acknowledged"] is True:
            search_omero_app.logger.info(
                "INDEX MAPPING SUCCESS FOR INDEX:", response["index"]
            )
        # catch API error response
    elif "error" in response:
        error = response["error"]
        search_omero_app.logger.info("ERROR:" + error["root_cause"])
        search_omero_app.logger.info("TYPE:" + error["type"])
        return False


def delete_es_index(es_index):
    es = search_omero_app.config.get("es_connector")
    saved_incies = get_all_indexes_from_elasticsearch()
    if es_index in saved_incies:
        response = es.indices.delete(index=es_index)
        if "acknowledged" in response:
            if response["acknowledged"] is True:
                search_omero_app.logger.info(response)

        # catch API error response
        elif "error" in response:
            error = response["error"]
            search_omero_app.logger.info("ERROR:" + error["root_cause"])
            search_omero_app.logger.info("TYPE:" + error["type"])
            return False

        # print out the response:
        search_omero_app.logger.info("\nresponse:%s" % str(response))
    else:
        search_omero_app.logger.info("\nIndex %s is not found" % str(es_index))
        return False
    return True


def delete_data_from_index(resource):
    if resource_elasticsearchindex.get(resource) and resource != "all":
        es_index = resource_elasticsearchindex[resource]
        es = search_omero_app.config.get("es_connector")
        es.delete_by_query(index=es_index, body={"query": {"match_all": {}}})
    elif resource == "all":
        es = search_omero_app.config.get("es_connector")
        for resource_, es_index in resource_elasticsearchindex.items():
            es.delete_by_query(index=es_index, body={"query": {"match_all": {}}})
    else:
        search_omero_app.logger.info(
            "\nNo index is found for resource:%s" % str(resource)
        )
        return False


def delete_index(resource, es_index=None):
    if es_index:
        return delete_es_index(es_index)
    if resource_elasticsearchindex.get(resource) and resource != "all":
        es_index = resource_elasticsearchindex[resource]
        return delete_es_index(es_index)
    elif resource == "all":
        all_indcies = get_all_indexes()
        for es_index in all_indcies:
            delete_es_index(es_index)
        return True
    else:
        search_omero_app.logger.info(
            "\nNo index is found for resource:%s" % str(resource)
        )
        return False


def prepare_images_data(data, doc_type):
    data_record = [
        "id",
        "owner_id",
        "experiment",
        "group_id",
        "name",
        "description",
        "mapvalue_name",
        "mapvalue_value",
        "project_name",
        "project_id",
        "dataset_name",
        "dataset_id",
        "screen_id",
        "screen_name",
        "plate_id",
        "plate_name",
        "well_id",
        "wellsample_id",
    ]
    total = len(data.index)
    counter = 0
    data_to_be_inserted = {}
    for index, row in data.iterrows():
        counter += 1
        if counter % 100000 == 0:
            search_omero_app.logger.info(
                "Process:\
                {counter}/{total}".format(
                    counter=counter, total=total
                )
            )

        if row["id"] in data_to_be_inserted:
            row_to_insert = data_to_be_inserted[row["id"]]
        else:
            row_to_insert = {}
            row_to_insert["doc_type"] = doc_type
            for rcd in data_record:
                if rcd in ["mapvalue_name", "mapvalue_value"]:
                    continue
                row_to_insert[rcd] = row[rcd]

            row_to_insert["key_values"] = []
            data_to_be_inserted[row["id"]] = row_to_insert
        key_value = row_to_insert["key_values"]
        key_value.append(
            {
                "name": row["mapvalue_name"],
                "value": row["mapvalue_value"],
                "index": row["mapvalue_index"],
            }
        )

    return data_to_be_inserted


def prepare_data(data, doc_type):
    data_record = [
        "id",
        "owner_id",
        "group_id",
        "name",
        "description",
        "mapvalue_name",
        "mapvalue_value",
    ]
    total = len(data.index)
    counter = 0
    data_to_be_inserted = {}
    for index, row in data.iterrows():
        counter += 1
        if counter % 100000 == 0:
            search_omero_app.logger.info(
                "Process:\
                {counter}/{total}".format(
                    counter=counter, total=total
                )
            )

        if row["id"] in data_to_be_inserted:
            row_to_insert = data_to_be_inserted[row["id"]]
        else:
            row_to_insert = {}
            row_to_insert["doc_type"] = doc_type
            for rcd in data_record:
                if rcd in ["mapvalue_name", "mapvalue_value"]:
                    continue
                row_to_insert[rcd] = row.get(rcd)
            row_to_insert["key_values"] = []
            data_to_be_inserted[row["id"]] = row_to_insert
        key_value = row_to_insert["key_values"]
        key_value.append(
            {
                "name": row["mapvalue_name"],
                "value": row["mapvalue_value"],
                "index": row["mapvalue_index"],
            }
        )

    return data_to_be_inserted


def handle_file(file_name, es_index, cols, is_image, from_json):
    co = 0
    search_omero_app.logger.info("Reading the csv file")
    if not from_json:
        df = pd.read_csv(file_name).replace({np.nan: None})
        search_omero_app.logger.info("setting the columns")
        df.columns = cols
        search_omero_app.logger.info("Prepare the data...")
        if not is_image:
            data_to_be_inserted = prepare_data(df, es_index)
        else:
            data_to_be_inserted = prepare_images_data(df, es_index)
        # print (data_to_be_inserted)
        search_omero_app.logger.info(len(data_to_be_inserted))
        with open(file_name + ".json", "w") as outfile:
            json.dump(data_to_be_inserted, outfile)

    else:
        search_omero_app.logger.info("Reading %s" % file_name)
        with open(file_name) as json_file:
            data_to_be_inserted = json.load(json_file)
    actions = []
    bulk_count = 0
    for k, record in data_to_be_inserted.items():
        co += 1
        bulk_count += 1
        if co % 10000 == 0:
            search_omero_app.logger.info(
                "Adding:  %s out of %s" % (co, len(data_to_be_inserted))
            )

        actions.append(
            {
                "_index": es_index,
                "_source": record  # ,
                # "_id": record['id']
            }
        )
    es = search_omero_app.config.get("es_connector")
    helpers.bulk(es, actions)


def get_file_list(path_name):
    from os import walk

    f = []
    for dirpath, dirnames, filenames in walk(path_name):
        f.extend(filenames)

    return f


def insert_resource_data(folder, resource, from_json):
    search_omero_app.logger.info(
        "Adding data to\
        {} using {}".format(
            resource, folder
        )
    )
    if not resource_elasticsearchindex.get(resource):
        search_omero_app.logger.info(
            "No index found for\
            resource: %s"
            % resource
        )
        return

    es_index = resource_elasticsearchindex.get(resource)
    if resource == "image":
        is_image = True
        cols = [
            "id",
            "owner_id",
            "experiment",
            "group_id",
            "name",
            "description",
            "mapvalue_name",
            "mapvalue_value",
            "mapvalue_index",
            "project_name",
            "project_id",
            "dataset_name",
            "dataset_id",
            "screen_id",
            "screen_name",
            "plate_id",
            "plate_name",
            "well_id",
            "wellsample_id",
        ]
    else:
        is_image = False
        if resource == "well":
            cols = [
                "id",
                "owner_id",
                "group_id",
                "mapvalue_name",
                "mapvalue_value",
                "mapvalue_index",
            ]
        else:
            cols = [
                "id",
                "owner_id",
                "group_id",
                "name",
                "description",
                "mapvalue_name",
                "mapvalue_value",
                "mapvalue_index",
            ]
    f_con = 0
    if os.path.isfile(folder):
        files_list = [folder]
    elif os.path.isdir(folder):
        files_list = get_file_list(folder)
    else:
        search_omero_app.logger.info(
            "No valid folder ({folder}) is provided ".format(folder=folder)
        )
        return
    for fil in files_list:
        fil = fil.strip()
        if from_json and not fil.endswith(".json"):
            continue
        n = len(files_list)
        search_omero_app.logger.info("%s==%s == %s" % (f_con, fil, n))
        file_name = os.path.join(folder, fil)
        handle_file(file_name, es_index, cols, is_image, from_json)
        search_omero_app.logger.info("File: %s has been processed" % fil)
        try:
            with open(file_name + ".done", "w") as outfile:
                json.dump(f_con, outfile)
        except Exception:
            search_omero_app.logger.info("Error .... writing Done file ...")
        f_con += 1


total_process = 0


def get_insert_data_to_index(sql_st, resource, dry_run=False):
    """
    - Query the postgreSQL database server and get metadata (key-value pair)
    - Process the results data
    - Insert them to the elasticsearch
    - Use multiprocessing to reduce the indexing time
    - If dry_run is true, the data will not be inserted to elasticsearch index
    These are performed using multiprocessing pool to reduce
    the indexing time by using parallel processing.
    """
    from datetime import datetime

    if not dry_run:
        delete_index(resource)
        create_omero_indexes(resource)
    sql_ = "select max (id) from %s" % resource
    res2 = search_omero_app.config["database_connector"].execute_query(sql_)
    max_id = res2[0].get("max", 0)
    if max_id is None:
        max_id = 0
    page_size = search_omero_app.config.get("CACHE_ROWS", 1000)
    start_time = datetime.now()
    cur_max_id = page_size
    vals = []
    # Prepare the multiprocessing data
    while True:
        vals.append((cur_max_id, (cur_max_id - page_size), resource, dry_run))
        if cur_max_id > max_id:
            break
        cur_max_id += page_size
    global total_process
    total_process = len(vals)
    # Determine the number of processes inside the multiprocessing pool,
    # i.e the number of allowed processors to run at the same time
    # It depends on the number of the processors that the hosting machine has
    if dry_run:
        no_processors = 1
    else:
        no_processors = search_omero_app.config.get("NO_PROCESSES")
        if not no_processors:
            no_processors = int(multiprocessing.cpu_count() / 2)
    search_omero_app.logger.info(
        "Number of the allowed parallel\
        processes inside the pool: %s"
        % no_processors
    )
    # create the multiprocessing pool
    pool = multiprocessing.Pool(no_processors)
    try:
        manager = multiprocessing.Manager()
        # a lock which will be used between the processes in the pool
        lock = manager.Lock()
        # a counter which will be used by the processes in the pool
        counter_val = manager.Value("i", 0)
        func = partial(processor_work, lock, counter_val)
        # map the data which will be consumed by the processes inside the pool
        res = pool.map(func, vals)
        search_omero_app.logger.info(cur_max_id)
        delta = str(datetime.now() - start_time)
        search_omero_app.logger.info("Total time=%s" % delta)
        print(res)
    finally:
        pool.close()


def processor_work(lock, global_counter, val):
    """
    A method to do the work inside a process within the multiprocessing pool
    """
    cur_max_id = val[0]
    range = val[1]
    resource = val[2]
    dry_run = val[3]
    search_omero_app.logger.info("%s, %s, %s" % (cur_max_id, range, resource))
    from omero_search_engine.cache_functions.elasticsearch.sql_to_csv import (
        sqls_resources,
    )

    sql_st = sqls_resources.get(resource)
    try:
        lock.acquire()
        global_counter.value += 1
    finally:
        lock.release()
    whereclause = " where %s.id < %s and %s.id >= %s" % (
        resource,
        cur_max_id,
        resource,
        range,
    )
    mod_sql = sql_st.substitute(whereclause=whereclause)
    st = datetime.now()
    search_omero_app.logger.info(
        "Calling the databas for %s/%s" % (global_counter.value, total_process)
    )
    conn = search_omero_app.config["database_connector"]
    results = conn.execute_query(mod_sql)
    search_omero_app.logger.info("Processing the results...")
    process_results(results, resource, global_counter, lock, dry_run)
    average_time = (datetime.now() - st) / 2
    search_omero_app.logger.info("Done")
    search_omero_app.logger.info("elpased time:%s" % average_time)


def process_results(results, resource, global_counter, lock=None, dry_run=False):
    df = pd.DataFrame(results).replace({np.nan: None})
    insert_resource_data_from_df(df, resource, global_counter, dry_run, lock)


def insert_resource_data_from_df(df, resource, global_counter, dry_lock, lock=None):
    if resource == "image":
        is_image = True
    else:
        is_image = False
    es_index = resource_elasticsearchindex.get(resource)
    search_omero_app.logger.info("Prepare the data...")
    if not is_image:
        data_to_be_inserted = prepare_data(df, es_index)
    else:
        data_to_be_inserted = prepare_images_data(df, es_index)
    # print (data_to_be_inserted)
    search_omero_app.logger.info(len(data_to_be_inserted))

    actions = []
    bulk_count = 0
    co = 0
    for k, record in data_to_be_inserted.items():
        co += 1
        bulk_count += 1
        if co % 40000 == 0:
            search_omero_app.logger.info(
                "Adding:  %s out of %s" % (co, len(data_to_be_inserted))
            )

        actions.append({"_index": es_index, "_source": record})  # ,
    if dry_lock:
        try:
            base_folder = "/etc/searchengine/"
            if not os.path.isdir(base_folder):
                base_folder = os.path.expanduser("~")
            json_file_name = "data_{counter}.json".format(counter=global_counter.value)
            json_file = os.path.join(base_folder, json_file_name)

            data_string = json.dumps(actions, indent=4)
            with open(json_file, "w") as the_file:
                the_file.write(data_string)

        except Exception as e:
            search_omero_app.logger.info("Error: %s" % str(e))
            print(json.dumps(actions, indent=4))
    else:
        es = search_omero_app.config.get("es_connector")
        search_omero_app.logger.info("Pushing the data to the Elasticsearch")
        try:
            lock.acquire()
            res = helpers.bulk(es, actions)
            search_omero_app.logger.info("Pushing results: %s" % str(res))

        except Exception as err:
            search_omero_app.logger.info("Error: %s" % str(err))
            raise err

        finally:
            lock.release()

        search_omero_app.logger.info("Added to search engine")


def insert_project_data(folder, project_file):
    file_name = folder + "\\" + project_file
    es_index = "project_keyvalue_pair_metadata"
    cols = [
        "id",
        "owner_id",
        "group_id",
        "name",
        "description",
        "mapvalue_name",
        "mapvalue_value",
    ]
    handle_file(file_name, es_index, cols)


def insert_screen_data(folder, screen_file):
    file_name = folder + "\\" + screen_file
    es_index = "screen_keyvalue_pair_metadata"
    cols = [
        "id",
        "owner_id",
        "group_id",
        "name",
        "description",
        "mapvalue_name",
        "mapvalue_value",
    ]
    handle_file(file_name, es_index, cols)


def insert_well_data(folder, well_file):
    file_name = folder + "\\" + folder
    es_index = "well_keyvalue_pair_metadata"
    cols = ["id", "owner_id", "group_id", "name", "mapvalue_name", "mapvalue_value"]
    handle_file(file_name, es_index, cols)


def insert_plate_data(folder, plate_file):
    file_name = folder + "\\" + plate_file
    es_index = "plate_keyvalue_pair_metadata"
    cols = [
        "id",
        "owner_id",
        "group_id",
        "name",
        "description",
        "mapvalue_name",
        "mapvalue_value",
    ]
    handle_file(file_name, es_index, cols)


def save_key_value_buckets(
    resource_table_=None, re_create_index=False, only_values=False
):
    """
    Query the database and get all available keys and values for
    the resource e.g. image,
    then query the elastic search to get value buckets for each bucket
    It will use multiprocessing pool to use parallel processing

    """
    es_index = "key_value_buckets_information"
    es_index_2 = "key_values_resource_cach"

    if re_create_index:
        if not only_values:
            search_omero_app.logger.info(
                "Try to delete if exist:  %s " % delete_es_index(es_index)
            )
            search_omero_app.logger.info(
                "Creaing key_value_buckets_informatio: %s"
                % create_index(es_index, key_value_buckets_info_template)
            )
        search_omero_app.logger.info(
            "Try to delete if exist: %s" % delete_es_index(es_index_2)
        )
        search_omero_app.logger.info(
            "Creating key_values_resource_cach: %s"
            % create_index(es_index_2, key_values_resource_cache_template)
        )

    for resource_table, linkedtable in annotation_resource_link.items():
        if resource_table_:
            if resource_table_ != resource_table:
                continue

        search_omero_app.logger.info(
            "check table:\
            %s ......."
            % resource_table
        )
        resource_keys = get_keys(resource_table)
        name_results = None
        if resource_table in ["project", "screen"]:
            sql = "select id, name,description  from {resource}".format(
                resource=resource_table
            )
            conn = search_omero_app.config["database_connector"]
            name_result = conn.execute_query(sql)
            # name_results = [res["name"] for res in name_results]
            # Determine the number of images for each container
            for res in name_result:
                id = res.get("id")
                if resource_table == "project":
                    sql_n = query_images_in_project_id.substitute(project_id=id)
                elif resource_table == "screen":
                    sql_n = query_images_screen_id.substitute(screen_id=id)
                no_images_co = conn.execute_query(sql_n)
                res["no_images"] = len(no_images_co)

            name_results = [
                {
                    "id": res["id"],
                    "description": res["description"],
                    "name": res["name"],
                    "no_images": res["no_images"],
                }
                for res in name_result
            ]

        push_keys_cache_index(resource_keys, resource_table, es_index_2, name_results)
        if only_values:
            continue
        search_omero_app.logger.info(
            "Resourse: {resource} has {no} attributes".format(
                resource=resource_table, no=len(resource_keys)
            )
        )
        vals = []
        # prepare the data which will be consumed by the processes
        # inside the multiprocessing Pool
        for key in resource_keys:
            vals.append((key, resource_table, es_index, len(resource_keys)))
        # determine the number of processes inside the process pool
        no_processors = search_omero_app.config.get("NO_PROCESSES")
        if not no_processors:
            no_processors = int(multiprocessing.cpu_count() / 2)
        search_omero_app.logger.info(
            "No of the allowed parallel processes: %s" % no_processors
        )
        pool = multiprocessing.Pool(no_processors)
        try:
            manager = multiprocessing.Manager()
            lock = manager.Lock()
            counter_val = manager.Value("i", 0)
            func = partial(save_key_value_buckets_process, lock, counter_val)
            res = pool.map(func, vals)
            print(res)
        finally:
            pool.close()


def save_key_value_buckets_process(lock, global_counter, vals):
    """
    It is used to perfom the indexing is a separate process
    inside the multiprocessing Pool
    """
    key = vals[0]
    resource_table = vals[1]
    es_index = vals[2]
    total = vals[3]
    wrong_keys = {}
    try:
        lock.acquire()
        global_counter.value += 1
    finally:
        lock.release()
    try:
        search_omero_app.logger.info(
            "Processing \
            %s/%s"
            % (global_counter.value, total)
        )
        search_omero_app.logger.info("Checking {key}".format(key=key))
        data_to_be_pushed = get_buckets(key, resource_table, es_index, lock)
        actions = []
        search_omero_app.logger.info(
            "data_to_be_pushed:\
            %s"
            % len(data_to_be_pushed)
        )
        for record in data_to_be_pushed:
            actions.append({"_index": es_index, "_source": record})
        es = search_omero_app.config.get("es_connector")
        search_omero_app.logger.info("Pushing to elasticsearch")
        try:
            lock.acquire()
            search_omero_app.logger.info(helpers.bulk(es, actions))
        except Exception as e:
            search_omero_app.logger.info("Error:  %s" % str(e))
            # raise e
        finally:
            lock.release()
    except Exception as e:
        search_omero_app.logger.info(
            "%s, \
            Error:%s "
            % (global_counter.value, str(e))
        )
        if wrong_keys.get(resource_table):
            wrong_keys[resource_table] = wrong_keys[resource_table].append(key)
        else:
            wrong_keys[resource_table] = [key]


def get_keys(res_table):
    sql = "select  distinct (name) from annotation_mapvalue\
           inner join {res_table}annotationlink on\
           {res_table}annotationlink.child=\
           annotation_mapvalue.annotation_id".format(
        res_table=res_table
    )
    results = search_omero_app.config["database_connector"].execute_query(sql)
    results = [res["name"] for res in results]
    return results


def push_keys_cache_index(results, resource, es_index, resourcename=None):
    row = {}
    row["name"] = results
    row["doc_type"] = es_index
    row["resource"] = resource
    if resourcename:
        row["resourcename"] = resourcename

    search_omero_app.logger.info("data_to_be_pushed: %s" % len(row))
    actions = []
    actions.append({"_index": es_index, "_source": row})
    es = search_omero_app.config.get("es_connector")
    search_omero_app.logger.info(helpers.bulk(es, actions))


def get_buckets(key, resourcse, es_index, lock=None):
    try:
        lock.acquire()
        res = get_all_values_for_a_key(resourcse, key)
    finally:
        lock.release()
    search_omero_app.logger.info(
        "number of bucket: %s" % res.get("total_number_of_buckets")
    )
    data_to_be_pushed = prepare_bucket_index_data(res, resourcse, es_index)
    return data_to_be_pushed


def prepare_bucket_index_data(results, res_table, es_index):
    data_to_be_inserted = []
    for result in results.get("data"):
        row = {}
        data_to_be_inserted.append(row)
        row["id"] = uuid.uuid4()
        row["resource"] = res_table
        row["Attribute"] = result["Key"]
        row["doc_type"] = es_index
        row["Value"] = result["Value"]
        row["items_in_the_bucket"] = result["Number of %ss" % res_table]
        row["total_buckets"] = results["total_number_of_buckets"]
        row["total_items_in_saved_buckets"] = results["total_number"]
        row["total_items"] = results["total_number_of_%s" % res_table]
    return data_to_be_inserted


def determine_cashed_bucket(attribute, resource, es_indrx):
    res = query_cashed_bucket(attribute, resource, es_indrx)
    search_omero_app.logger.info(res)
