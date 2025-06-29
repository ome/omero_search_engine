import os
import click
from omero_search_engine import create_app

# from flask_script import Manager
from configurations.configuration import (
    update_config_file,
    delete_data_source_configuration,
    rename_datasource,
)

search_omero_app = create_app()


@search_omero_app.cli.command("show_saved_indices")
def show_saved_indices():
    from omero_search_engine.cache_functions.elasticsearch.transform_data import (  # noqa
        get_all_indexes,
    )

    all_indexes = get_all_indexes()
    click.echo(all_indexes)


@search_omero_app.cli.command("delete_es_index")
@click.option(
    "-r",
    "--resource",
    default="all",
    help="resource name, deleting all the indexes for all the resources is the default",  # noqa
)
@click.option(
    "-e",
    "--es_index",
    default=None,
    help="elastic index name, if it is provided, it will delete and return",
)
def delete_es_index(resource, es_index):
    from omero_search_engine.cache_functions.elasticsearch.transform_data import (  # noqa
        delete_index,
    )

    delete_index(resource, es_index)


@search_omero_app.cli.command("delete_all_data_from_es_index")
@click.option(
    "-r",
    "--resource",
    default=None,
    help="resource name, deleting all data from the its related index",
)
def delete_all_data_from_es_index(resource):
    from omero_search_engine.cache_functions.elasticsearch.transform_data import (
        delete_data_from_index,
    )

    delete_data_from_index(resource)


@search_omero_app.cli.command("add_resource_data_to_es_index")
@click.option("-r", "--resource", default=None, help="resource name, e.g. image")
@click.option(
    "-d", "--data_folder", default=None, help="Folder contains the data files"
)
@click.option("-f", "--from_json", default=False, help="Folder contains the data files")
def add_resource_data_to_es_index(resource, data_folder, from_json):
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


@search_omero_app.cli.command("create_index")
@click.option(
    "-r",
    "--resource",
    default="all",
    help="resource name, creating all the indexes for all the resources is the default",  # noqa
)
def create_index(resource):
    """
    Create Elasticsearch index for each resource
    """
    from omero_search_engine.cache_functions.elasticsearch.transform_data import (
        create_omero_indexes,
    )

    create_omero_indexes(resource)


@search_omero_app.cli.command("restore_postgresql_database")
@click.option(
    "-s",
    "--source",
    default="all",
    help="data source name, restore all the data sources by default",  # noqa
)
def restore_postgresql_database(source):
    from omero_search_engine.database.utils import restore_database

    restore_database(source)


@search_omero_app.cli.command("get_index_data_from_database")
@click.option(
    "-r",
    "--resource",
    default="all",
    help="resource name, creating all the indexes for all the resources is the default",  # noqa
)
@click.option(
    "-d",
    "--data_source",
    default="all",
    help="data source name, indexing all the data sources by default",  # noqa
)
@click.option(
    "-b",
    "--backup",
    default=True,
    help="if True, backup will be called ",  # noqa
)
def get_index_data_from_database(resource, data_source, backup):
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

        test_indexing_search_query("app_data/test_index_data.json", data_source_, "False", "True")


    # backup the index data
    if backup:
        backup_elasticsearch_data()


@search_omero_app.cli.command("backup_elasticsearch_data")
def backup_elasticsearch_data():
    from omero_search_engine.cache_functions.elasticsearch.backup_restores import (
        backup_indices_data,
    )

    backup_indices_data()


# set configurations
@search_omero_app.cli.command("set_database_configuration")
@click.option("-u", "--url", default=None, help="database server url")
@click.option("-s", "--server_port_number", default=None, help="database port number")
@click.option("-d", "--database", default=None, help="database name")
@click.option("-n", "--name", default=None, help="database usernname")
@click.option("-b", "--backup_filename", default=None, help="database backup filename")
@click.option("-p", "--password", default=None, help="database username password")
@click.option("-w", "--working_data_source", default=None, help="data source")
def set_database_configuration(
    working_data_source,
    url,
    server_port_number,
    database,
    backup_filename,
    name,
    password,
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


@search_omero_app.cli.command("set_default_datasource")
@click.option("-d", "--default_data_source", default=None, help="Default data source")
def set_default_datasource(default_data_source):
    if default_data_source:
        update_config_file({"DEFAULT_DATASOURCE": default_data_source})
    else:
        search_omero_app.logger.info("No attribute provided")


################################################################
@search_omero_app.cli.command("set_data_source_files")
@click.option("-n", "--name", default=None, help="data source name")
@click.option(
    "-i",
    "--images_folder",
    default=None,
    help="path to a folder containing the CSV files containing the image data ",
)
@click.option(
    "-p",
    "--projects_file",
    default=None,
    help="path to a file containing the projects data",
)
@click.option(
    "-s",
    "--screens_file",
    default=None,
    help="path to a file containing the screens data",
)
@click.option(
    "-o", "--origin_type", default=None, help="data source origin  type; supports CSV"
)
def set_data_source_files(
    name,
    images_folder,
    projects_file,
    screens_file,
    origin_type,
):
    source = {}
    if not name:
        print("Source name attribute is missing")
        return
    source["name"] = name
    source_attrs = {}
    source["CSV"] = source_attrs
    source_attrs["type"] = origin_type
    if images_folder:
        source_attrs["images_folder"] = images_folder
    if projects_file:
        source_attrs["projects_file"] = projects_file
    if screens_file:
        source_attrs["screens_file"] = screens_file

    update_config_file(source, True)


###############################################################################


@search_omero_app.cli.command("rename_data_source")
@click.option("-n", "--new_data_source_name", default=None, help="new data source name")
@click.option(
    "-c", "--current_data_source_name", default=None, help="original data source name"
)
def rename_data_source(current_data_source_name, new_data_source_name):
    if not current_data_source_name or not new_data_source_name:
        search_omero_app.logger.info(
            "Existing data source name and new data source name are required"
        )
        return
    rename_datasource(current_data_source_name, new_data_source_name)


@search_omero_app.cli.command("set_elasticsearch_configuration")
@click.option("-e", "--elasticsearch_url", default=None, help="elasticsearch url")
def set_elasticsearch_configuration(elasticsearch_url):
    if elasticsearch_url:
        update_config_file({"ELASTICSEARCH_URL": elasticsearch_url})
    else:
        search_omero_app.logger.info("No attribute is provided")


@search_omero_app.cli.command("set_verify_certs")
@click.option("-v", "--verify_certs", default=None, help="set verify certs")
def set_verify_certs(verify_certs):
    if verify_certs:
        update_config_file({"verify_certs": verify_certs})
    else:
        search_omero_app.logger.info("No attribute is provided")


@search_omero_app.cli.command("set_elasticsearch_backup_folder")
@click.option(
    "-b", "--backup_folder", default=None, help="path to elasticsearch backup folder"
)
def set_elasticsearch_backup_folder(backup_folder):
    if backup_folder:
        update_config_file({"ELASTICSEARCH_BACKUP_FOLDER": backup_folder})
    else:
        search_omero_app.logger.info("No elasticsearch backup folder is provided")


@search_omero_app.cli.command("set_idr_test_file")
@click.option("-i", "--idr_url", default=None, help="URL for idr test file")
def set_idr_test_file(idr_url):
    if idr_url:
        update_config_file({"IDR_TEST_FILE_URL": idr_url})
    else:
        search_omero_app.logger.info("No attribute is provided")


@search_omero_app.cli.command("set_cache_rows_number")
@click.option("-n", "--number_cache_rows", default=None, help="cache folder path")
def set_cache_rows_number(number_cache_rows):
    if number_cache_rows and number_cache_rows.isdigit():
        update_config_file({"CACHE_ROWS": int(number_cache_rows)})
    else:
        search_omero_app.logger.info("No of cached rows has to be an integer")


@search_omero_app.cli.command("set_searchengine_secret_key")
@click.option("-s", "--secret_key", default=None, help="cache folder path")
def set_searchengine_secret_key(secret_key):
    if secret_key:
        update_config_file({"SECRET_KEY": secret_key})
    else:
        search_omero_app.logger.info("No value is provided")


@search_omero_app.cli.command("set_max_page")
@click.option("-s", "--page_size", default=None, help="Page size")
def set_max_page(page_size):
    if page_size and page_size.isdigit():
        update_config_file({"PAGE_SIZE": int(page_size)})
    else:
        search_omero_app.logger.info("No valid attribute is provided")


@search_omero_app.cli.command("set_no_processes")
@click.option("-n", "--no_processes", default=None, help="no_processes")
def set_no_processes(no_processes):
    if no_processes and no_processes.isdigit():
        update_config_file({"NO_PROCESSES": int(no_processes)})
    else:
        search_omero_app.logger.info("No valid attribute is provided")


@search_omero_app.cli.command("cache_key_value_index")
@click.option(
    "-d",
    "--data_source",
    default="all",
    help="data source name, the default is all",  # noqa
)
@click.option(
    "-r",
    "--resource",
    default=None,
    help="resource name, creating all the indexes for all the resources is the default",  # noqa
)
@click.option(
    "-c",
    "--create_index",
    default=None,
    help="creating the elastic search index if set to True",  # noqa
)
@click.option("-o", "--only_values", default=None, help="creating cached values only ")
def cache_key_value_index(resource, data_source, create_index, only_values):
    """
    Cache the value bucket for each value for each resource
    """
    from omero_search_engine.cache_functions.elasticsearch.transform_data import (
        save_key_value_buckets,
    )

    save_key_value_buckets(resource, data_source, create_index, only_values)


@search_omero_app.cli.command("test_indexing_search_query")
@click.option(
    "-j",
    "--json_file",
    default="app_data/test_index_data.json",
    help="creating cached values only ",
)
@click.option("-c", "--check_studies", default=False, help="check studies from idr ")
@click.option(
    "-d",
    "--deep_check",
    default=False,
    help="compare all the images from both search engine and database server, default is False so it will compare the number of images and the first searchengine page",  # noqa
)
@click.option(
    "-s",
    "--source",
    default=None,
    help="data source name, testing  all the data sources by default",  # noqa
)
def test_indexing_search_query(
    json_file,
    source,
    deep_check,
    check_studies,
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

##################################
@search_omero_app.cli.command("restore_elasticsearch_data")
def restore_elasticsearch_data():
    from omero_search_engine.cache_functions.elasticsearch.backup_restores import (
        restore_indices_data,
    )

    # first delete the current indices
    delete_es_index("all")
    restore_indices_data()


@search_omero_app.cli.command("data_validator")
@click.option("-s", "--screen_name", default=None, help="Screen name, or part of it")
@click.option("-p", "--project_name", default=None, help="Project name, or part of it")
def data_validator(screen_name, project_name):
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


@search_omero_app.cli.command("test_container_key_value")
def test_container_key_value():
    from omero_search_engine.validation.results_validator import (
        check_container_keys_vakues,
    )

    check_container_keys_vakues()


@search_omero_app.cli.command("get_index_data_from_csv_files")
@click.option(
    "-d",
    "--datasource",
    default=None,
    help="data source name, indexing all the data sources by default",  # noqa
)
@click.option(
    "-f",
    "--folder",
    default=None,
    help="data folder containing the CSV files",  # noqa
)
@click.option(
    "-r",
    "--resource",
    default="image",
    help="resource name, creating all the indexes for all the resources by default",  # noqa
)
@click.option(
    "-n",
    "--need_convert",
    default=False,
    help="if the CSV files are generating from CSV templates, this attribute must be true",  # noqa
)
@click.option("-u", "--update_cache", default=False, help="update the cache")
def get_index_data_from_csv_files(
    datasource,
    folder,
    resource,
    need_convert,
    update_cache,
):
    from omero_search_engine.cache_functions.elasticsearch.transform_data import (
        insert_resource_data,
        # save_key_value_buckets,
    )

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
    else:
        from omero_search_engine.api.v1.resources.utils import delete_data_source_cache

        delete_data_source_cache(datasource)


@search_omero_app.cli.command("convert_to_searchengine_format")
@click.option(
    "-f",
    "--file_name",
    default=None,
    help="The CSV file name",  # noqa
)
@click.option(
    "-r",
    "--resource",
    default=None,
    help="resource name, creating all the indexes for all the resources by default",  # noqa
)
def convert_to_searchengine_format(file_name, resource):
    from omero_search_engine.cache_functions.elasticsearch.transform_data import (
        convert_to_searchengine_format,
    )

    converted_file_name = convert_to_searchengine_format(file_name, resource)
    search_omero_app.logger.info(
        "The file has been successfully converted. "
        "The name of the converted file is: %s" % converted_file_name
    )


@search_omero_app.cli.command("delete_containers")
@click.option(
    "-r", "--resource", default=None, help="resource name, i.e. project or screen"
)
@click.option(
    "-d",
    "--synchronous_run",
    default=False,
    help="synchronous run, either True of False, "
    "it should be False for large containers",
)
@click.option(
    "-s", "--data_source", default=None, help="data_source name, i.e. project or screen"
)
@click.option(
    "-i",
    "--id",
    default=None,
    help="Resource id, if more than one then should use comma to separate them",
)
@click.option("-u", "--update_cache", default=False, help="update the cache")
def delete_containers(
    resource,
    data_source,
    id,
    update_cache,
    synchronous_run,
):
    """
    delete a container (project or screen)
    if it is required to delete more than container:
     ids should be separated by comma

    """
    from omero_search_engine.api.v1.resources.utils import delete_container

    delete_container(id, resource, data_source, update_cache, synchronous_run)


@search_omero_app.cli.command("index_container_from_database")
@click.command
@click.option("-r", "--resource", default=None, help="resource name, e.g. image")
@click.option(
    "-d", "--data_source", default=None, help="data_source name, i.e. project or screen"
)
@click.option(
    "-i",
    "--id",
    default=None,
    help="Resource id, if more than one then use comma to  separate the values",
)
@click.option(
    "-b",
    "--backup",
    default=False,
    help="if True, backup will be called ",  # noqa
)
@click.option("-u", "--update_cache", default=False, help="update the cache")
@click.option(
    "-n", "--number_of_processors", default=2, help="Number of parallel processes"
)
def index_container_from_database(
    resource,
    data_source,
    id,
    backup,
    update_cache,
    number_of_processors,
):
    resources_index = {
        "project": ["image", "project"],
        "screen": ["image", "screen", "well", "plate"],
    }
    from omero_search_engine.cache_functions.elasticsearch.transform_data import (
        index_containers_from_database,
    )

    # from omero_search_engine.api.v1.resources.utils import update_data_source_cache

    import time

    for res in resources_index[resource]:
        index_containers_from_database(
            resource, res, id, data_source, number_of_processors
        )
        time.sleep(60)

    if update_cache:
        update_data_source_cache(data_source)
    else:
        delete_data_source_cache(data_source)

    # backup the index data
    if backup:
        backup_elasticsearch_data()
    time.sleep(60)


@search_omero_app.cli.command("update_data_source_cache")
@click.option("-d", "--working_data_source", default=None, help="data source")
def update_data_source_cache(data_source):
    from omero_search_engine.api.v1.resources.utils import update_data_source_cache

    if not data_source:
        print("Data source is required")
        return
    update_data_source_cache(data_source)


@search_omero_app.cli.command("delete_data_source_cache")
@click.option("-d", "--working_data_source", default=None, help="data source")
def delete_data_source_cache(data_source):
    if not data_source:
        print("Data source is required")
        return
    from omero_search_engine.api.v1.resources.utils import delete_data_source_cache

    delete_data_source_cache(data_source)


@search_omero_app.cli.command("delete_data_source")
@click.option("-d", "--data_source", default=None, help="data source")
def delete_data_source(data_source):
    if not data_source:
        print("Data source is required")
        return
    from omero_search_engine.api.v1.resources.utils import delete_data_source_contents

    found = delete_data_source_contents(data_source)
    if found:
        delete_data_source_configuration(data_source)


@search_omero_app.cli.command("set_automatic_refresh")
@click.option(
    "-a",
    "--automatic_refresh",
    default=True,
    help="set automatic refresh, if true any change of "
    "the configuration file will be reloaded at runtime, default  is true",
)
def set_automatic_refresh(automatic_refresh):
    update_config_file({"AUTOMATIC_REFRESH": automatic_refresh})


# export FLASK_APP=commands.py
