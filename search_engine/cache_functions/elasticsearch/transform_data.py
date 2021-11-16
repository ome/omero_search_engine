from search_engine import search_omero_app
from elasticsearch import  helpers
import os
import pandas as pd
import numpy as np
import json

def create_index(es_index, template):
    es=search_omero_app.config.get("es_connector")
    try:
        response = es.indices.create(index=es_index, body=template)

        if 'acknowledged' in response:
            if response['acknowledged'] == True:
                search_omero_app.logger.info("INDEX MAPPING SUCCESS FOR INDEX: %s"% response['index'])
        # catch API error response
        elif 'error' in response:
            search_omero_app.logger.info("ERROR: %s"% response['error']['root_cause'])
            search_omero_app.logger.info("TYPE: %s"% response['error']['type'])
            return False
    except Exception as ex:
        search_omero_app.logger.info("Error while creating index {es_index}, error message: {error}".format(es_index=es_index, error=str(ex)))
        return False

    # print out the response:
    #search_omero_app.logger.info('\nresponse:'+ str(response))
    return True



def create_omero_indexes():
    from search_engine.cache_functions.elasticsearch.elasticsearch_templates import image_template, non_image_template
    from search_engine.api.v2.resources.utils import resource_elasticsearchindex
    for resourse, es_index in resource_elasticsearchindex.items():
        if resourse=='image':
            template=image_template
        else:
            template=non_image_template

        search_omero_app.logger.info(f"Creating index {es_index} for {resourse}".format(es_index=es_index, resourse=resourse))
        create_index(es_index, template)



def get_all_indexes():
    es=search_omero_app.config.get("es_connector")
    all_indexes = es.indices.get('*')
    return all_indexes

def rename_index(old_index, new_index):
    es = search_omero_app.config.get("es_connector")
    response = es.indices.reindex(source=old_index, dest=new_index)
    if 'acknowledged' in response:
        if response['acknowledged'] == True:
            search_omero_app.logger.info("INDEX MAPPING SUCCESS FOR INDEX:", response['index'])
        # catch API error response
    elif 'error' in response:
        search_omero_app.logger.info("ERROR:" + response['error']['root_cause'])
        search_omero_app.logger.info("TYPE:" + response['error']['type'])
        return False


def delete_index(es_index):
    es=search_omero_app.config.get("es_connector")
    response = es.indices.delete(index=es_index)
    if 'acknowledged' in response:
        if response['acknowledged'] == True:
            search_omero_app.logger.info(response)

    # catch API error response
    elif 'error' in response:
        search_omero_app.logger.info("ERROR:"+ response['error']['root_cause'])
        search_omero_app.logger.info("TYPE:"+ response['error']['type'])
        return False

    # print out the response:
    search_omero_app.logger.info('\nresponse:%s' %str(response))


def prepare_images_data (data, doc_type):
    data_record=["id", "owner_id", "experiment", "group_id", "name", "mapvalue_name", "mapvalue_value", "project_name",
     "project_id", "dataset_name", "dataset_id", "screen_id", "screen_name", "plate_id", "plate_name", "well_id",
     "wellsample_id"]
    total = len(data.index)
    counter=0
    data_to_be_inserted={}
    for index, row in data.iterrows():
        counter+=1
        if counter % 100 == 0:
            search_omero_app.logger.info ("Process : {counter}/{total}".format(counter=counter, total=total))

        if row["id"] in data_to_be_inserted:
            row_to_insert=data_to_be_inserted[row["id"]]
        else:
            row_to_insert = {}
            row_to_insert["doc_type"] = doc_type
            for rcd in data_record:
                if rcd in ["mapvalue_name", "mapvalue_value"]:
                    continue
                row_to_insert[rcd] = row[rcd]

            row_to_insert["key_values"]=[]
            data_to_be_inserted[row["id"]] = row_to_insert
        key_value=row_to_insert["key_values"]
        key_value.append({"name": row["mapvalue_name"], "value":row["mapvalue_value"]})

    return data_to_be_inserted


def prepare_data (data, doc_type):
    data_record = ["id", "owner_id", "group_id", "name", "mapvalue_name", "mapvalue_value"]
    total = len(data.index)
    counter=0
    data_to_be_inserted={}
    for index, row in data.iterrows():
        counter+=1
        if counter % 1000 == 0:
            search_omero_app.logger.info ("Process : {counter}/{total}".format(counter=counter, total=total))

        if row["id"] in data_to_be_inserted:
            row_to_insert=data_to_be_inserted[row["id"]]
        else:
            row_to_insert = {}
            row_to_insert["doc_type"] = doc_type
            for rcd in data_record:
                if rcd in ["mapvalue_name", "mapvalue_value"]:
                    continue
                row_to_insert[rcd] = row[rcd]
            row_to_insert["key_values"] = []
            data_to_be_inserted[row["id"]] = row_to_insert
        key_value=row_to_insert["key_values"]
        key_value.append({"name": row["mapvalue_name"], "value":row["mapvalue_value"]})

    return data_to_be_inserted

def handle_file(file_name, es_index, cols, is_image=False):

    co = 0
    '''
    search_omero_app.logger.info ("Reading the csv file")
    df = pd.read_csv(file_name).replace({np.nan: None})
    search_omero_app.logger.info ("setting the columns")
    df.columns=cols
    search_omero_app.logger.info ("Prepare the data...")
    if not is_image:
        data_to_be_inserted=prepare_data(df,es_index)
    else:
        data_to_be_inserted=prepare_images_data(df,es_index)
    #print (data_to_be_inserted)
    search_omero_app.logger.info (len(data_to_be_inserted))
    with open(file_name+".txt", 'w') as outfile:
        json.dump(data_to_be_inserted, outfile)
    '''
    search_omero_app.logger.info ("Reading %s"% file_name)

    with open(file_name) as json_file:
        data_to_be_inserted = json.load(json_file)
    actions=[]
    bulk_count=0
    for k, record in data_to_be_inserted.items():
        co += 1
        bulk_count+=1
        if co % 1000 == 0:
            search_omero_app.logger.info("Adding:  %s out of %s"%(co, len(data_to_be_inserted)))

        actions.append(
              {
                 "_index":es_index,
                "_source": record#,
                #"_id": record['id']
              }
        )

    es = search_omero_app.config.get("es_connector")
    helpers.bulk(es, actions)


def get_file_list(path_name):
    from os import walk
    f = []
    for (dirpath, dirnames, filenames) in walk(path_name):
        f.extend(filenames)

    return f

def insert_resourse_data(folder, es_index):
    search_omero_app.logger.info("Adding data to {} using {}".format(es_index, folder))
    if "image" in es_index:
        is_image=True
        cols = ["id", "owner_id", "experiment", "group_id", "name", "mapvalue_name", "mapvalue_value", "project_name",
                "project_id", "dataset_name", "dataset_id", "screen_id", "screen_name", "plate_id", "plate_name",
                "well_id", "wellsample_id"]
    else:
        is_image=False
        cols=["id", "owner_id", "group_id", "name", "mapvalue_name", "mapvalue_value"]
    f_con=0

    #folder=r"D:\data\all_images\final\complter_images_data"#D:\data\all_images\final"
    if os.path.isfile(folder):
        files_list=[folder]
    elif os.path.isdir(folder):
        files_list=get_file_list(folder)
    else:
        search_omero_app.logger.info("No valid folder ({folder}) is provided ".format(folder=folder))
        return
    for fil in files_list:
        fil=fil.strip()
        if not fil.endswith(".txt"):
            continue
        search_omero_app.logger.info ("%s==%s == %s"%(f_con,fil,len(files_list)))
        file_name=os.path.join(folder,fil)
        handle_file(file_name, es_index, cols, is_image)
        search_omero_app.logger.info("File: %s has been processed"%fil)
        try:
            with open(file_name + ".done", 'w') as outfile:
                json.dump(f_con, outfile)
        except:
            pass
        f_con+=1


def insert_project_data(folder, project_file):
    #folder = r"D:\data\all_images\final"
    #project_file="project_sorted_ids.csv"
    file_name = folder + "\\" + project_file
    es_index="project_keyvalue_pair_metadata"
    #cols = ["id", "o   wner_id", "experiment", "group_id", "permissions", "image_name", "mapvalue_name", "mapvalue_value"]
    cols =["id","owner_id","group_id","name","mapvalue_name","mapvalue_value"]

    handle_file(file_name, es_index, cols)

def insert_screen_data(folder, screen_file):
    #project_file="screen_sorted_ids.csv"
    #folder = r"D:\data\all_images\final"
    file_name = folder + "\\" + screen_file
    es_index="screen_keyvalue_pair_metadata"
    #cols = ["id", "owner_id", "experiment", "group_id", "permissions", "image_name", "mapvalue_name", "mapvalue_value"]
    cols =["id","owner_id","group_id","name","mapvalue_name","mapvalue_value"]
    handle_file(file_name, es_index, cols)

def insert_well_data(folder, well_file):
    #folder = r"D:\data\all_images\final"
    #well_file="well_sorted_ids.csv"
    file_name = folder + "\\" + folder
    es_index="well_keyvalue_pair_metadata"
    #cols = ["id", "owner_id", "experiment", "group_id", "permissions", "image_name", "mapvalue_name", "mapvalue_value"]
    cols =["id","owner_id","group_id","name","mapvalue_name","mapvalue_value"]

    handle_file(file_name, es_index, cols)

def insert_plate_data(folder, plate_file):
    #folder = r"D:\data\all_images\final"
    #plate_file="plate_sorted_ids.csv"
    file_name = folder + "\\" + plate_file
    es_index="plate_keyvalue_pair_metadata"
    #cols = ["id", "owner_id", "experiment", "group_id", "permissions", "image_name", "mapvalue_name", "mapvalue_value"]
    cols =["id","owner_id","group_id","name","mapvalue_name","mapvalue_value"]
    handle_file(file_name, es_index, cols)




path_name=r"D:\data\New_idr_database\images_data"
