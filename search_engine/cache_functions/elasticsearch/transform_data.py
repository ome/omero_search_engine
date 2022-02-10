from search_engine import search_omero_app
from elasticsearch import  helpers
import  pandas as pd
import numpy as np
import os
from search_engine.api.v2.resources.utils import resource_elasticsearchindex
from search_engine.cache_functions.elasticsearch.elasticsearch_templates import image_template, non_image_template

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

    return True

def  create_omero_indexes(resource):
    if resource!="all" and not resource_elasticsearchindex.get(resource):
        search_omero_app.logger.info("No index template found for resource: %s"%resource)

    for resource_, es_index in resource_elasticsearchindex.items():
        if  resource != 'all' and resource_ != resource:
            print (resource_, resource)
            continue
        if resource_== 'image':
            template=image_template
        else:
            template=non_image_template
        search_omero_app.logger.info(f"Creating index {es_index} for {resource_}".format(es_index=es_index, resource=resource_))
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

def delete_es_index(es_index):
    es = search_omero_app.config.get("es_connector")
    response = es.indices.delete(index=es_index)
    if 'acknowledged' in response:
        if response['acknowledged'] == True:
            search_omero_app.logger.info(response)

    # catch API error response
    elif 'error' in response:
        search_omero_app.logger.info("ERROR:" + response['error']['root_cause'])
        search_omero_app.logger.info("TYPE:" + response['error']['type'])
        return False
    # print out the response:
    search_omero_app.logger.info('\nresponse:%s' % str(response))
    return True

def delte_data_from_index(resource):
    if resource_elasticsearchindex.get(resource) and resource!="all":
        es_index=resource_elasticsearchindex[resource]
        #print ("All data inside Index for resource %s will be deleted, continue y/n?"%resource)
        #choice = input().lower()
        #if choice!="y" and choice!="yes":
        #    return False
        es = search_omero_app.config.get("es_connector")
        es.delete_by_query(index=es_index, body={"query": {"match_all": {}}})
    elif resource=="all":
        es = search_omero_app.config.get("es_connector")
        for resource_, es_index in resource_elasticsearchindex.items():
            es.delete_by_query(index=es_index, body={"query": {"match_all": {}}})
    else:
        search_omero_app.logger.info('\nNo index is found for resource:%s' %str(resource))
        return False

def delete_index(resource):
    if resource_elasticsearchindex.get(resource) and resource!="all":
        es_index=resource_elasticsearchindex[resource]
        #print ("Index for resource %s will be deleted, continue y/n?"%resource)
        #choice = input().lower()
        #if choice!="y" and choice!="yes":
        #    return False
        #print("Are you sure ")
        return delete_es_index(es_index)
    elif resource=="all":
        for resource_, es_index in resource_elasticsearchindex.items():
            delete_es_index(es_index)
        return True
    else:
        search_omero_app.logger.info('\nNo index is found for resource:%s' %str(resource))
        return False

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
        key_value.append({"name": row["mapvalue_name"], "value":row["mapvalue_value"], "index":row["mapvalue_index"]})

    return data_to_be_inserted


def prepare_data (data, doc_type):
    data_record = ["id", "owner_id", "group_id", "name", "mapvalue_name", "mapvalue_value"]
    total = len(data.index)
    counter=0
    data_to_be_inserted={}
    for index, row in data.iterrows():
        counter+=1
        if counter % 10000 == 0:
            search_omero_app.logger.info ("Process : {counter}/{total}".format(counter=counter, total=total))

        if row["id"] in data_to_be_inserted:
            row_to_insert=data_to_be_inserted[row["id"]]
        else:
            row_to_insert = {}
            row_to_insert["doc_type"] = doc_type
            for rcd in data_record:
                if rcd in ["mapvalue_name", "mapvalue_value"]:
                    continue
                row_to_insert[rcd] = row.get(rcd)
            row_to_insert["key_values"] = []
            data_to_be_inserted[row["id"]] = row_to_insert
        key_value=row_to_insert["key_values"]
        key_value.append({"name": row["mapvalue_name"], "value":row["mapvalue_value"], "index":row["mapvalue_index"]})

    return data_to_be_inserted

def handle_file(file_name, es_index, cols, is_image,from_json):
    co = 0
    search_omero_app.logger.info ("Reading the csv file")
    if not from_json:
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
        with open(file_name+".json", 'w') as outfile:
            json.dump(data_to_be_inserted, outfile)

    else:
        search_omero_app.logger.info ("Reading %s"% file_name)
        with open(file_name) as json_file:
            data_to_be_inserted = json.load(json_file)
    actions=[]
    bulk_count=0
    for k, record in data_to_be_inserted.items():
        co += 1
        bulk_count+=1
        if co % 10000 == 0:
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

def insert_resource_data(folder, resource, from_json):
    search_omero_app.logger.info("Adding data to {} using {}".format(resource, folder))
    if not resource_elasticsearchindex.get(resource):
        search_omero_app.logger.info("No index found for resource: %s"%resource)
        return

    es_index=resource_elasticsearchindex.get(resource)
    if resource=="image":
        is_image=True
        cols = ["id", "owner_id", "experiment", "group_id", "name", "mapvalue_name", "mapvalue_value", "mapvalue_index", "project_name",
                "project_id", "dataset_name", "dataset_id", "screen_id", "screen_name", "plate_id", "plate_name",
                "well_id", "wellsample_id"]
    else:
        is_image=False
        if resource=="well":
            cols=["id", "owner_id", "group_id", "mapvalue_name", "mapvalue_value","mapvalue_index"]
        else:
            cols = ["id", "owner_id", "group_id", "name", "mapvalue_name", "mapvalue_value", "mapvalue_index"]
    f_con=0
    if os.path.isfile(folder):
        files_list=[folder]
    elif os.path.isdir(folder):
        files_list=get_file_list(folder)
    else:
        search_omero_app.logger.info("No valid folder ({folder}) is provided ".format(folder=folder))
        return
    for fil in files_list:
        fil=fil.strip()
        if from_json and not fil.endswith('.json'):
            continue
        search_omero_app.logger.info ("%s==%s == %s"%(f_con,fil,len(files_list)))
        file_name=os.path.join(folder,fil)
        handle_file(file_name, es_index, cols, is_image, from_json)
        search_omero_app.logger.info("File: %s has been processed"%fil)
        try:
            with open(file_name + ".done", 'w') as outfile:
                json.dump(f_con, outfile)
        except:
            print ("Error .... writing Done file ...")
        f_con+=1

def get_insert_data_to_index(sql_st, resource):
    '''
    - Query the postgressql database server and get metadata (key-value pair)
     -Process the resulted data
    - Insert them to the elasticsearch
    '''
    from datetime import datetime
    #delete the data from the index before trying to insert the data again
    #It will delete the index and create it again
    delete_index(resource)
    create_omero_indexes(resource)
    sql_="select max (id) from %s"%resource
    res2 = search_omero_app.config["database_connector"].execute_query(sql_)
    max_id=res2[0]["max"]
    page_size=search_omero_app.config["CACHE_ROWS"]
    start_time=datetime.now()
    cur_max_id=page_size
    no_=0
    total=0
    while True:
        no_+=1
        search_omero_app.logger.info("Run no: %s"%no_)
        whereclause= " where %s.id < %s and %s.id >= %s" % (resource, cur_max_id, resource, (cur_max_id - page_size))
        mod_sql=sql_st.substitute(whereclause=whereclause)
        st=datetime.now()
        results=search_omero_app.config["database_connector"].execute_query (mod_sql)
        search_omero_app.logger.info("Processing the results...")
        process_results(results, resource)
        total+=len(results)
        search_omero_app.logger.info ("Run no: %s, return: %s, total: %s"%(no_, len(results),total))
        search_omero_app.logger.info("elpased time:%s"%str(datetime.now()-st))
        if cur_max_id>max_id:
            break
        cur_max_id+=page_size
    search_omero_app.logger.info (cur_max_id)
    search_omero_app.logger.info ("Total time=%s"%str(datetime.now()-start_time))

def process_results(results,resource):
    df = pd.DataFrame(results).replace({np.nan: None})
    insert_resource_data_from_df(df, resource)


def insert_resource_data_from_df(df, resource, ):
    if resource=="image":
        is_image=True
    else:
        is_image=False
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
    co=0
    for k, record in data_to_be_inserted.items():
        co += 1
        bulk_count += 1
        if co % 10000 == 0:
            search_omero_app.logger.info("Adding:  %s out of %s" % (co, len(data_to_be_inserted)))

        actions.append(
            {
                "_index": es_index,
                "_source": record  # ,
            }
        )
    es = search_omero_app.config.get("es_connector")
    helpers.bulk(es, actions)



def insert_project_data(folder, project_file):
    file_name = folder + "\\" + project_file
    es_index="project_keyvalue_pair_metadata"
    cols =["id","owner_id","group_id","name","mapvalue_name","mapvalue_value"]
    handle_file(file_name, es_index, cols)

def insert_screen_data(folder, screen_file):
    file_name = folder + "\\" + screen_file
    es_index="screen_keyvalue_pair_metadata"
    cols =["id","owner_id","group_id","name","mapvalue_name","mapvalue_value"]
    handle_file(file_name, es_index, cols)

def insert_well_data(folder, well_file):
    file_name = folder + "\\" + folder
    es_index="well_keyvalue_pair_metadata"
    cols =["id","owner_id","group_id","name","mapvalue_name","mapvalue_value"]
    handle_file(file_name, es_index, cols)

def insert_plate_data(folder, plate_file):
    file_name = folder + "\\" + plate_file
    es_index="plate_keyvalue_pair_metadata"
    cols =["id","owner_id","group_id","name","mapvalue_name","mapvalue_value"]
    handle_file(file_name, es_index, cols)




path_name=r"D:\data\New_idr_database\images_data"
