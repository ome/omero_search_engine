import os
import json
from search_engine import search_omero_app
from flask_script import Manager

manager = Manager(search_omero_app)
#create_app()

from search_engine.cache_functions.hdf_cache_funs import update_cash, cash_values,  delete_cashed_key, check_cashed_query


@manager.command
def set_resource_cash_name_value():
    ''''
    cah names and values for each resource (e.g image, project)
    '''
    cash_values()


@manager.command
def update_cash_files():
    '''
    cash metadata names for each resource (e.g. image, project) and save them in hdf5 file format
    '''
    update_cash()


@manager.command
def delete_cashed_key_value():
    resource_table="image"
    key="Cell Line"#"Gene Symbol"
    value=None#"Normal tissue, NOS"#"KIF11"

    delete_cashed_key(resource_table, key, value)


@manager.command
def show_saved_index():
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
@manager.option('-r', '--resourse', help='resourse name, e.g. image')
@manager.option('-d', '--data_folder', help='Folder contains the data files')
def add_resourse_data_to_es_index(resourse=None, data_folder=None):
    '''
     Insert data inside elastic search index by getting the data from csv files
    '''
    from search_engine.cache_functions.elasticsearch.transform_data import insert_resourse_data
    insert_resourse_data(data_folder, resourse)

@manager.command
@manager.option('-r', '--resourse', help='resourse name, creating all the indcese for all the resources is the default')
def create_index(resourse="all"):
    '''
    Create Elasticsearch index for each resource
    '''
    from search_engine.cache_functions.elasticsearch.transform_data import create_omero_indexes
    create_omero_indexes(resourse)



if __name__ == '__main__':
    manager.run()