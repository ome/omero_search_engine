import os
import json
from search_engine import search_omero_app
from flask_script import Manager

manager = Manager(search_omero_app)
#create_app()

from search_engine.cache_functions.hdf_cache_funs import update_cash, cash_values,  delete_cashed_key, check_cashed_query
from search_engine.cache_functions.elasticsearch.sql_to_csv import create_csv_for_images, create_csv_for_non_images
@manager.command
def update_annotation_namevalue():
    cash_values()
    already_updated = []
    file_name = 'updated.csv'
    if os.path.exists(file_name):
        outfile = open(file_name, 'r')
        ss = outfile.read()
        outfile.close()
        already_updated=ss.split("\n")
    sql="select id from annotation where discriminator='/map/'"
    ids=search_omero_app.config["database_connector"].execute_query(sql)
    print (len(ids), type(ids[0]),ids[0].get('id'))
    count=0
    for id_ in ids:
        id=id_.get('id')
        print ("Processing  {id},  {count}/ {l}".format(id=id,count=count, l=len(ids)))
        count+=1
        if str(id) in already_updated:
            print ("It is found and processed")
            continue
        #print ("Processing  {id},  {count}/ {l}".format(id=id,count=count, l=len(ids)))
        sql_1="select name, value from annotation_mapvalue where annotation_id ={id}  ".format(id=id)
        print (sql_1)
        results=search_omero_app.config["database_connector"].execute_query(sql_1)
        print ("Results obtained")
        if len(results)==0:
            continue
        jsonb=[]
        for result in results:
            print (result)
            temp_dict={}
            temp_dict['name']=result.get('name')
            temp_dict['value']=result.get('value')
            jsonb.append(temp_dict)

        sql_2="update annotation set namevalue= '{jsonb}' where id = {id}".format(id=id,jsonb=json.dumps(jsonb) )
        search_omero_app.config["database_connector"].execute_query(sql_2, return_results=False)
        outfile = open(file_name, 'a')
        outfile.newlines
        outfile.write(str(id)+"\n")
        print ("File is updated ")
        outfile.close()
        print ("File is closaeds")


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
def read_cashed_value():
    table="image"
    name="Cell Line"
    value="HeLa"

    name="Gene Symbol"
    value="NCAPD2"
    name="Cell Cycle Phase"
    value="anaphase"
    name="Antibody Identifier"
    value="CAB034889"

    name="Organism Part Identifier"
    value="T-77100	"
    name = "Organism"
    vale = "Part Prostate"
    val = check_cashed_query(table, name, value)
    if val:
        print (len(val))
    else:
        print ("No cached results")

@manager.command
def show_saved_index():
    from search_engine.cache_functions.elasticsearch.transform_data import  get_all_indexes
    all_indexes=get_all_indexes()
    for index in all_indexes:
        print ("Index: ==>>>",index)
    return (all_indexes)


@manager.command
def delete_es_index():
    from search_engine.cache_functions.elasticsearch.transform_data import  delete_index
    delete_index("image_keyvalue_pair_metadata_new")

@manager.command
@manager.option('-r', '--resourse_index', help='resourse_index')
@manager.option('-f', '--data_folder', help='Folder contains the data files')
def add_resourse_data_to_es_index(resourse_index=None, data_folder=None):
    '''
     Insert data inside elastic search index by getting the data from csv files
    '''
    from search_engine.cache_functions.elasticsearch.transform_data import insert_resourse_data
    insert_resourse_data(data_folder, resourse_index)

@manager.command
def create_index():
    '''
    Create Elasticsearch index for each resource
    '''
    from search_engine.cache_functions.elasticsearch.transform_data import create_omero_indexes
    create_omero_indexes()

@manager.command
@manager.option('-f', '--data_folder', help='Folder is the local folder where the data files are saved')
def create_csv_for_images_now(folder=None):
    create_csv_for_images(folder)


@manager.command
@manager.option('-r', '--csv_data_file', help='csv file whihc contains the data')
@manager.option('-f', '--resource', help='table, e.g project, screen')
def create_csv_for_non_images_now(resource="screen",csv_data_file=None):
    create_csv_for_non_images(resource, csv_data_file)

if __name__ == '__main__':
    manager.run()