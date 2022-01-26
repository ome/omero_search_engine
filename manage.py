import os
import json
from search_engine import search_omero_app
from flask_script import Manager

from configurations.configuration import update_config_file

manager = Manager(search_omero_app)

from search_engine.cache_functions.hdf_cache_funs import update_cached, cached_values,  delete_cacheded_key, cached_project_names, cached_project_names


@manager.command

@manager.option('-t', '--table_resourse', help='resourse name to cache, if it is not provided all resources will be cached')

def set_resource_cached_name_value(table_resourse=None):
    ''''
    cah names and values for each resource (e.g image, project)
    '''
    cached_values(table_resourse)


@manager.command
def update_cached_files():
    '''
    cached metadata names for each resource (e.g. image, project) and save them in hdf5 file format
    '''
    update_cached()

@manager.command
def cached_names():
    cached_project_names("project")


@manager.command
def delete_cacheded_key_value():
    resource_table="image"
    key="Cell Line"#"Gene Symbol"
    value=None#"Normal tissue, NOS"#"KIF11"

    delete_cacheded_key(resource_table, key, value)


@manager.command
def show_saved_indices():
    from search_engine.cache_functions.elasticsearch.transform_data import  get_all_indexes
    all_indexes=get_all_indexes()
    for index in all_indexes:
        print ("Index: ==>>>",index)
    return (all_indexes)

@manager.command
@manager.option('-r', '--resourse', help='resourse name, deleting all the indcese for all the resources is the default')
def delete_es_index(resourse='all'):
    from search_engine.cache_functions.elasticsearch.transform_data import  delete_index
    delete_index(resourse)

@manager.command
@manager.option('-r', '--resourse', help='resourse name, deleting all data from the its related index')
def delete_all_data_from_es_index(resourse='None'):
    from search_engine.cache_functions.elasticsearch.transform_data import  delte_data_from_index
    delte_data_from_index(resourse)

@manager.command
@manager.option('-r', '--resourse', help='resourse name, e.g. image')
@manager.option('-d', '--data_folder', help='Folder contains the data files')
@manager.option('-f', '--from_json', help='Folder contains the data files')
#D:\data\New_idr_database\image_data\image_33\test
def add_resourse_data_to_es_index(resourse=None, data_folder=None,from_json=False):
    ''' =
     Insert data inside elastic search index by getting the data from csv files
    '''
    if not resourse or not data_folder or not os.path.exists(data_folder):
        search_omero_app.logger.info("Please check the input parameters, resourse: {resourse}, data_folder: {data_folder}".format(resourse=resourse, data_folder=data_folder))
        return
    from search_engine.cache_functions.elasticsearch.transform_data import insert_resourse_data
    insert_resourse_data(data_folder, resourse, from_json)

@manager.command
@manager.option('-r', '--resourse', help='resourse name, creating all the indcese for all the resources is the default')
def create_index(resourse="all"):
    '''
    Create Elasticsearch index for each resource
    '''
    from search_engine.cache_functions.elasticsearch.transform_data import create_omero_indexes
    create_omero_indexes(resourse)

def sql_results_to_panda():
    pass

@manager.command
@manager.option('-r', '--resourse', help='resourse name, creating all the indcese for all the resources is the default')
def get_index_data_from_database(resourse="all"):
    '''
    insert data in Elasticsearch index for each resource
    It gets the data from postgres database server
    '''
    from search_engine.cache_functions.elasticsearch.sql_to_csv import sqls_resources
    from search_engine.cache_functions.elasticsearch.transform_data import   get_insert_data_to_index

    if resourse!="all":
        sql_st=sqls_resources.get(resourse)
        if not sql_st:
            return
        get_insert_data_to_index(sql_st, resourse)
    else:
        for res, sql_st in sqls_resources.items():
            get_insert_data_to_index(sql_st, res)


##set configurations
@manager.command
@manager.option('-u', '--url', help='database server url')
@manager.option('-s', '--server_port_number', help='database port number')
@manager.option('-d', '--database', help='database name')
@manager.option('-n', '--name', help='database usernname')
@manager.option('-p', '--password', help='database username password')
def set_database_configuration(url=None, server_port_number=None, database=None,name=None, password=None):
    database_attrs={}
    if url:
        database_attrs["DATABASE_SERVER_URI"]=url
    if database:
        database_attrs["DATABAS_NAME"]=database
    if name:
        database_attrs["DATABASE_USER"]=name
    if password:
        database_attrs["DATABASE_PASSWORD"]=password
    if server_port_number and server_port_number.isdigit():
        database_attrs["DATABASE_PORT"] = server_port_number

    if len(database_attrs)>0:
        update_config_file(database_attrs)
    else:
        search_omero_app.logger.info("At least one database attributed (i.e. url, database name, username, username password) should be provided")



@manager.command
@manager.option('-e', '--elasticsearch_url', help='elasticsearch url')
def set_elasticsearch_configuration(elasticsearch_url=None):
    if elasticsearch_url:
        update_config_file({"ELASTICSEARCH_URL":elasticsearch_url})
    else:
        search_omero_app.logger.info("No attribute is provided")

@manager.command
@manager.option('-c', '--cache_folder', help='cache folder path')
def set_cache_folder (cache_folder=None):
    if cache_folder:
        update_config_file({"CACHE_FOLDER":cache_folder})
    else:
        search_omero_app.logger.info("No attribute is provided")

@manager.command
@manager.option('-s', '--page_size', help='cache folder path')
def set_max_page(page_size=None):
    if page_size and page_size.isdigit():
        update_config_file({"PAGE_SIZE":int(page_size)})
    else:
        search_omero_app.logger.info("No valid attribute is provided")



if __name__ == '__main__':
    manager.run()