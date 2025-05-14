#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

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

import os

from omero_search_engine import search_omero_app, create_app
from flask_script import Manager
from configurations.configuration import (
    update_config_file,
    delete_data_source_configuration,
    rename_datasource,
)

manager = Manager(search_omero_app)


@manager.command
def show_saved_indices():
    from omero_search_engine.cache_functions.elasticsearch.transform_data import (  # noqa
        get_all_indexes,
    )

    all_indexes = get_all_indexes()
    return all_indexes


@manager.command
@manager.option(
    "-r",
    "--resource",
    help="resource name, deleting all the indexes for all the resources is the default",  # noqa
)
@manager.option(
    "-e",
    "--es_index",
    help="elastic index name, if it is provided, it will delete and return",
)
def delete_es_index(resource="all", es_index=None):
    from omero_search_engine.cache_functions.elasticsearch.transform_data import (  # noqa
        delete_index,
    )

    delete_index(resource, es_index)


@manager.command
@manager.option(
    "-r",
    "--resource",
    help="resource name, deleting all data from the its related index",
)
def delete_all_data_from_es_index(resource="None"):
    from omero_search_engine.cache_functions.elasticsearch.transform_data import (
        delete_data_from_index,
    )

    delete_data_from_index(resource)


@manager.command
@manager.option("-r", "--resource", help="resource name, e.g. image")
@manager.option("-d", "--data_folder", help="Folder contains the data files")
@manager.option("-f", "--from_json", help="Folder contains the data files")
def add_resource_data_to_es_index(resource=None, data_folder=None, from_json=False):
    """
    Insert data inside elastic search index by getting the data from csv files
    """
    from omero_search_engine.cache_functions.elasticsearch.transform_data import (
        insert_resource_data,
    )

    if not resource or not data_folder or not os.path.exists(data_folder):
        search_omero_app.logger.info(
            "Please check the input parameters, resource:\
            {resource}, data_folder: {data_folder}".format(
                resource=resource, data_folder=data_folder
            )
        )
        return
    insert_resource_data(data_folder, resource, from_json)


@manager.command
@manager.option(
    "-r",
    "--resource",
    help="resource name, creating all the indexes for all the resources is the default",  # noqa
)
def create_index(resource="all"):
    """
    Create Elasticsearch index for each resource
    """
    from omero_search_engine.cache_functions.elasticsearch.transform_data import (
        create_omero_indexes,
    )

    create_omero_indexes(resource)


def sql_results_to_panda():
    pass


@manager.command
@manager.option(
    "-s",
    "--source",
    help="data source name, restore all the data sources by default",  # noqa
)
def restore_postgresql_database(source="all"):
    from omero_search_engine.database.utils import restore_database

    restore_database(source)


@manager.command
@manager.option(
    "-r",
    "--resource",
    help="resource name, creating all the indexes for all the resources is the default",  # noqa
)
@manager.option(
    "-d",
    "--data_source",
    help="data source name, indexing all the data sources by default",  # noqa
)
@manager.option(
    "-d",
    "--backup",
    help="if True, backup will be called ",  # noqa
)
def get_index_data_from_database(resource="all", data_source="all", backup="True"):
    """
    insert data in Elasticsearch index for each resource
    It gets the data from postgres database server
    """
    from omero_search_engine.cache_functions.elasticsearch.sql_to_csv import (
        sqls_resources,
    )
    from omero_search_engine.cache_functions.elasticsearch.transform_data import (
        get_insert_data_to_index,
        save_key_value_buckets,
    )
    import json

    backup = json.loads(backup.lower())
    if not data_source:
        print("Data source is required to process")
        return
    elif data_source == "all":
        clean_index = True

    else:
        clean_index = False
    for data_source_ in search_omero_app.config.database_connectors.keys():
        if data_source.lower() != "all" and data_source_.lower() != data_source.lower():
            continue

        for res, sql_st in sqls_resources.items():
            if resource.lower() != "all" and resource.lower() != res.lower():
                continue
            get_insert_data_to_index(sql_st, res, data_source_, clean_index)
        save_key_value_buckets(
            resource_table_=None,
            data_source=data_source_,
            clean_index=clean_index,
            only_values=False,
        )
        print(
            "Done for data_source: %s from %s"
            % (data_source_, search_omero_app.config.database_connectors.keys())
        )
        if clean_index:
            clean_index = False

        # validate the indexing

        test_indexing_search_query(
            source=data_source_, deep_check=False, check_studies=True
        )

    # backup the index data
    if backup:
        backup_elasticsearch_data()


# set configurations
@manager.command
@manager.option("-u", "--url", help="database server url")
@manager.option("-s", "--server_port_number", help="database port number")
@manager.option("-d", "--database", help="database name")
@manager.option("-n", "--name", help="database usernname")
@manager.option("-b", "--backup_filename", help="database backup filename")
@manager.option("-p", "--password", help="database username password")
@manager.option("-w", "--working_data_source", help="data source")
def set_database_configuration(
    working_data_source=None,
    url=None,
    server_port_number=None,
    database=None,
    backup_filename=None,
    name=None,
    password=None,
):
    if not working_data_source:
        print("Data source is required to process")
    database_attrs = {}
    database_config = {}
    database_config["name"] = working_data_source
    database_config["DATABASE"] = database_attrs
    if database:
        database_attrs["DATABASE_NAME"] = database
    if url:
        database_attrs["DATABASE_SERVER_URI"] = url
    if name:
        database_attrs["DATABASE_USER"] = name
    if password:
        database_attrs["DATABASE_PASSWORD"] = password
    if server_port_number and server_port_number.isdigit():
        database_attrs["DATABASE_PORT"] = server_port_number
    if backup_filename:
        database_attrs["DATABASE_BACKUP_FILE"] = backup_filename

    if len(database_attrs) > 0:
        update_config_file(database_config, data_source=True)
    else:
        search_omero_app.logger.info(
            "At least one database attribute\
             (i.e. url, database name, username, username password)\
             should be provided"
        )


@manager.command
@manager.option("-d", "--default_database", help="Default data source")
def set_default_datasource(default_database=None):
    if default_database:
        update_config_file({"DEFAULT_DATASOURCE": default_database})
    else:
        search_omero_app.logger.info("No attribute is provided")


@manager.command
@manager.option("-n", "--name", help="data source name")
@manager.option(
    "-i",
    "--images_folder",
    help="path to a folder containing the CSV files containing the image data ",
)
@manager.option(
    "-p", "--projects_file", help="path to a file containing the projects data"
)
@manager.option(
    "-s", "--screens_file", help="path to a file containing the screens data"
)
@manager.option("-d", "--datasource_type", help=" data source type; supports CSV")
def set_data_source_files(
    name=None,
    images_folder=None,
    projects_file=None,
    screens_file=None,
    datasource_type="CSV",
):
    source = {}
    if not name:
        print("Source name attribute is missing")
        return
    source["name"] = name
    source_attrs = {}
    source["CSV"] = source_attrs
    source_attrs["type"] = datasource_type
    if images_folder:
        source_attrs["images_folder"] = images_folder
    if projects_file:
        source_attrs["projects_file"] = projects_file
    if screens_file:
        source_attrs["screens_file"] = screens_file

    update_config_file(source, True)


@manager.command
@manager.option("-n", "--new_data_source_name", help="new data source name")
@manager.option("-d", "--source_name", help="orginal data source name")
def rename_data_source(data_source=None, new_data_source_name=None):
    if not data_source or not new_data_source_name:
        search_omero_app.logger.info(
            "Existing data source name and new data source name are required"
        )
        return
    rename_datasource(data_source, new_data_source_name)


@manager.command
@manager.option("-e", "--elasticsearch_url", help="elasticsearch url")
def set_elasticsearch_configuration(elasticsearch_url=None):
    if elasticsearch_url:
        update_config_file({"ELASTICSEARCH_URL": elasticsearch_url})
    else:
        search_omero_app.logger.info("No attribute is provided")


@manager.command
@manager.option("-e", "--elasticsearch_password", help="set elasticsearch password")
def set_elasticsearch_password(elasticsearch_password=None):
    if elasticsearch_password:
        update_config_file({"ELASTIC_PASSWORD": elasticsearch_password})
    else:
        search_omero_app.logger.info("No attribute is provided")


@manager.command
@manager.option("-v", "--verify_certs", help="set elasticsearch password")
def set_verify_certs(verify_certs=None):
    if verify_certs:
        update_config_file({"verify_certs": verify_certs})
    else:
        search_omero_app.logger.info("No attribute is provided")


@manager.command
@manager.option("-c", "--cache_folder", help="cache folder path")
def set_cache_folder(cache_folder=None):
    if cache_folder:
        update_config_file({"CACHE_FOLDER": cache_folder})
    else:
        search_omero_app.logger.info("No attribute is provided")


@manager.command
@manager.option("-b", "--backup_folder", help="path to elasticsearch backup folder")
def set_elasticsearch_backup_folder(backup_folder=None):
    if backup_folder:
        update_config_file({"ELASTICSEARCH_BACKUP_FOLDER": backup_folder})
    else:
        search_omero_app.logger.info("No elasticsearch backup folder is provided")


@manager.command
@manager.option("-i", "--idr_url", help="URL for idr test file")
def set_idr_test_file(idr_url=None):
    if idr_url:
        update_config_file({"IDR_TEST_FILE_URL": idr_url})
    else:
        search_omero_app.logger.info("No attribute is provided")


@manager.command
@manager.option("-n", "--number_cache_rows", help="cache folder path")
def set_cache_rows_number(number_cache_rows=None):
    if number_cache_rows and number_cache_rows.isdigit():
        update_config_file({"CACHE_ROWS": int(number_cache_rows)})
    else:
        search_omero_app.logger.info("No of cached rows has to be an integer")


@manager.command
@manager.option("-s", "--secret_key", help="cache folder path")
def set_searchengine_secret_key(secret_key=None):
    if secret_key:
        update_config_file({"SECRET_KEY": secret_key})
    else:
        search_omero_app.logger.info("No value is provided")


@manager.command
@manager.option("-s", "--page_size", help="Page size")
def set_max_page(page_size=None):
    if page_size and page_size.isdigit():
        update_config_file({"PAGE_SIZE": int(page_size)})
    else:
        search_omero_app.logger.info("No valid attribute is provided")


@manager.command
@manager.option("-n", "--no_processes", help="no_processes")
def set_no_processes(no_processes=None):
    if no_processes and no_processes.isdigit():
        update_config_file({"NO_PROCESSES": int(no_processes)})
    else:
        search_omero_app.logger.info("No valid attribute is provided")


@manager.command
@manager.option(
    "-d",
    "--data_source",
    help="data source name, the default is all",  # noqa
)
@manager.option(
    "-r",
    "--resource",
    help="resource name, creating all the indexes for all the resources is the default",  # noqa
)
@manager.option(
    "-c",
    "--create_index",
    help="creating the elastic search index if set to True",  # noqa
)
@manager.option("-o", "--only_values", help="creating cached values only ")
def cache_key_value_index(
    resource=None, data_source="all", create_index=None, only_values=None
):
    """
    Cache the value bucket for each value for each resource
    """
    from omero_search_engine.cache_functions.elasticsearch.transform_data import (
        save_key_value_buckets,
    )

    save_key_value_buckets(resource, data_source, create_index, only_values)


@manager.command
@manager.option("-j", "--json_file", help="creating cached values only ")
@manager.option("-c", "--check_studies", help="check studies from idr ")
@manager.option(
    "-d",
    "--deep_check",
    help="compare all the images from both search engine and database server, default is False so it will compare the number of images and the first searchengine page",  # noqa
)
@manager.option(
    "-s",
    "--source",
    help="data source name, testing  all the data sources by default",  # noqa
)
def test_indexing_search_query(
    json_file="app_data/test_index_data.json",
    source=None,
    deep_check=False,
    check_studies=False,
):
    """
    test the indexing and the searchengine query functions
    can be used:
      * after the indexing to check the elasticsearch index data
      * after the code modifications to check the searchengine queries results
    The test data can be provided from external files,
    i.e. json file format
    if the data file, it will use sample file from
    (test_index_data.json) app_data folder
    """
    from omero_search_engine.validation.results_validator import (
        validate_queries,
        test_no_images,
        get_omero_stats,
        get_no_images_sql_containers,
    )

    if not source:
        print("Data source is required to process ")
        return

    validate_queries(json_file, source, deep_check)
    if check_studies:
        test_no_images(source)
    get_omero_stats()
    get_no_images_sql_containers(data_source=source)


@manager.command
def backup_elasticsearch_data():
    from omero_search_engine.cache_functions.elasticsearch.backup_restores import (
        backup_indices_data,
    )

    backup_indices_data()


@manager.command
def restore_elasticsearch_data():
    from omero_search_engine.cache_functions.elasticsearch.backup_restores import (
        restore_indices_data,
    )

    # first delete the current indices
    delete_es_index("all")
    restore_indices_data()


@manager.command
@manager.option("-s", "--screen_name", help="Screen name, or part of it")
@manager.option("-p", "--project_name", help="Project name, or part of it")
def data_validator(screen_name=None, project_name=None):
    """
    Checking key-value pair for trailing and heading space.
    It also checks the key-value pair duplication.
    It can check all the projects and screens.
    Also, it can run for a specific project or screen.
    The output is a collection of CSV files; each check usually generates three files:
    The main file contains image details (e.g. image id)
    in addition to the key and the value.
    one file for screens and one for projects.
    Each file contains the screen name (project name),
      the key-value pair which has the issue and the total number of affected
      images for each row.
    """
    from datetime import datetime

    if screen_name and project_name:
        print("Either screen name or project name is allowed")

    from omero_search_engine.validation.omero_keyvalue_data_validator import (
        check_for_heading_space,
        check_for_trailing_space,
        check_duplicated_keyvalue_pairs,
    )

    start = datetime.now()
    check_for_trailing_space(screen_name, project_name)
    start1 = datetime.now()
    check_for_heading_space(screen_name, project_name)
    start2 = datetime.now()
    check_duplicated_keyvalue_pairs(screen_name, project_name)
    end = datetime.now()
    print("start: %s, start1: %s, start2: %s, end: %s" % (start, start1, start2, end))


@manager.command
def test_container_key_value():
    from omero_search_engine.validation.results_validator import (
        check_container_keys_vakues,
    )

    check_container_keys_vakues()


@manager.command
@manager.option(
    "-d",
    "--datasource",
    help="data source name, indexing all the data sources by default",  # noqa
)
@manager.option(
    "-f",
    "--folder",
    help="data folder containing the CSV files",  # noqa
)
@manager.option(
    "-r",
    "--resource",
    help="resource name, creating all the indexes for all the resources is the default",  # noqa
)
@manager.option(
    "-n",
    "--need_convert",
    help="if the CSV files are generating from CSV templates, this attribute must be true",  # noqa
)
@manager.option("-u", "--update_cache", help="update the cache")
def get_index_data_from_csv_files(
    datasource=None,
    folder=None,
    resource="image",
    need_convert="False",
    update_cache="False",
):
    from omero_search_engine.cache_functions.elasticsearch.transform_data import (
        insert_resource_data,
        # save_key_value_buckets,
    )
    import json

    update_cache = json.loads(update_cache.lower())
    need_convert = json.loads(need_convert.lower())

    insert_resource_data(
        folder=folder,
        resource=resource,
        data_source=datasource,
        from_json=False,
        need_convert=need_convert,
    )
    search_omero_app.logger.info("Indexing data in progress...")

    import time

    time.sleep(60)
    if update_cache:
        update_data_source_cache(datasource)


@manager.command
@manager.option(
    "-f",
    "--file_name",
    help="The CSV file name",  # noqa
)
@manager.option(
    "-r",
    "--resource",
    help="resource name, creating all the indexes for all the resources by default",  # noqa
)
def convert_to_searchengine_indexer_format(file_name=None, resource=None):
    from omero_search_engine.cache_functions.elasticsearch.transform_data import (
        conver_to_searchengine_fromat,
    )

    converted_file_name = conver_to_searchengine_fromat(file_name, resource)
    print(converted_file_name)


@manager.command
@manager.option("-r", "--resource", help="resource name, i.e. project or screen")
@manager.option(
    "-d",
    "--synchronous_run",
    help="synchronous run, either True of False, "
    "it should be False for large containers",
)
@manager.option("-s", "--data_source", help="data_source name, i.e. project or screen")
@manager.option(
    "-i",
    "--id",
    help="Resource id, if more than one then should use comma to separate them",
)
@manager.option("-u", "--update_cache", help="update the cache")
def delete_containers(
    resource=None,
    data_source=None,
    id=None,
    update_cache="False",
    synchronous_run="False",
):
    """
    delete a container (project or screen)
    if it is required to delete more than container:
     ids should be separated by comma

    """
    from omero_search_engine.api.v1.resources.utils import delete_container
    import json

    ###
    synchronous_run = json.loads(synchronous_run.lower())
    update_cache = json.loads(update_cache.lower())
    ###
    delete_container(id, resource, data_source, update_cache, synchronous_run)


@manager.command
@manager.command
@manager.option("-r", "--resource", help="resource name, e.g. image")
@manager.option("-d", "--data_source", help="data_source name, i.e. project or screen")
@manager.option(
    "-i",
    "--id",
    help="Resource id, if more than one then use comma to  separate the values",
)
@manager.option(
    "-b",
    "--backup",
    help="if True, backup will be called ",  # noqa
)
@manager.option("-u", "--update_cache", help="update the cache")
@manager.option("-n", "--no_processors", help="allowed no of parallel processes")
def index_container_from_database(
    resource=None,
    data_source=None,
    id=None,
    backup="False",
    update_cache="False",
    no_processors=2,
):
    resources_index = {
        "project": ["image", "project"],
        "screen": ["image", "screen", "well", "plate"],
    }
    from omero_search_engine.cache_functions.elasticsearch.transform_data import (
        index_container_s_from_database,
    )

    # from omero_search_engine.api.v1.resources.utils import update_data_source_cache
    import json
    import time

    backup = json.loads(backup.lower())
    update_cache = json.loads(update_cache.lower())
    no_processors = int(no_processors)

    for res in resources_index[resource]:
        index_container_s_from_database(resource, res, id, data_source, no_processors)
        time.sleep(60)

    if update_cache:
        update_data_source_cache(data_source)

    # backup the index data
    if backup:
        backup_elasticsearch_data()
    time.sleep(60)


@manager.command
@manager.option("-d", "--working_data_source", help="data source")
def update_data_source_cache(data_source=None):
    from omero_search_engine.api.v1.resources.utils import update_data_source_cache

    if not data_source:
        print("Data source is required")
        return
    update_data_source_cache(data_source)


@manager.command
@manager.option("-d", "--data_source", help="data source")
def delete_data_source(data_source=None):
    if not data_source:
        print("Data source is required")
        return
    from omero_search_engine.api.v1.resources.utils import delete_data_source_contents

    found = delete_data_source_contents(data_source)
    if found:
        delete_data_source_configuration(data_source)


@manager.command
@manager.option(
    "-a",
    "--automatic_refresh",
    help="set automatic refresh, if true any change of "
    "the configuration file will be reloaded at runtime",
)
def set_automatic_refresh(automatic_refresh="True"):
    if not automatic_refresh:
        print("Error, no attribute value provided")

    automatic_refresh = json.loads((automatic_refresh.lower()))
    update_config_file({"AUTOMATIC_REFRESH": automatic_refresh})


if __name__ == "__main__":
    from flask_script import Command

    Command.capture_all_args = False
    create_app()
    manager.run()
