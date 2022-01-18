import sys
import h5py
import pandas as pd
from pandas import HDFStore,DataFrame# create (or open) an hdf5 file and opens in append mode
import os
import json
from app_data.data_attrs import annotation_resource_link
from search_engine import search_omero_app

cached_metadata="cached_metadata_h5py.h5"

def cached_project_names(resourse):
    cached_folder = search_omero_app.config["cached_FOLDER"]
    cached_file_name = os.path.join(cached_folder, 'names.h5')
    sql="select name from {resourse}".format(resourse=resourse)
    results = search_omero_app.config["database_connector"].execute_query(sql)
    results = [res['name'] for res in results]
    f = h5py.File(cached_file_name, 'w')
    try:
        g = f.create_group('names')
        d = g.create_dataset(resourse, data=json.dumps(results))
        f.close()
    except Exception as e:
        search_omero_app.logger.info("Error while writing the file  ...." + str(e))
        f.close()
        sys.exit(0)

def get_resource_names(resource_table):
    cached_folder = search_omero_app.config["cached_FOLDER"]
    cached_file_name = os.path.join(cached_folder, "names.h5")
    if not os.path.exists(cached_file_name):
        return []

    f = h5py.File(cached_file_name, "r")
    try:
        names = json.loads(
            f["names/{resource_table}".format(resource_table=resource_table)][()])
        f.close()
        return names
    except Exception as e:
        search_omero_app.logger.info("Error: " + str(e))
        f.close()
        return []

def get_file_name(table,name, operator=None):
    if not operator:
        file_name="{table}_{name}.h5".format(table=table, name=name)
    else:
        file_name = "{table}_{name}_{operator}.h5".format(table=table, name=name, operator=operator)
    return file_name

def read_cached_for_table (res_table):
    cached_folder = search_omero_app.config["CACHE_FOLDER"]
    metadata=None
    if res_table:
        cached_file_name = os.path.join(cached_folder, "annotation_names.h5")
        if not os.path.exists(cached_file_name):
            return metadata
        f= h5py.File(cached_file_name, "r")
        try:
            metadata = json.loads(
                f["keys"]["{resource_table}".format(resource_table=res_table)][()])
        except Exception as e:
            search_omero_app.logger.info ("Error reading "+str(e))
        f.close()
        return metadata

def update_cached():
    cached_folder = search_omero_app.config["cached_FOLDER"]
    cached_file_name = os.path.join(cached_folder, 'annotation_names.h5')
    f= h5py.File(cached_file_name, 'w')
    g = f.create_group('keys')
    for res_table in annotation_resource_link:
        sql="select  distinct (name) from annotation_mapvalue inner join {res_table}annotationlink on {res_table}annotationlink.child=annotation_mapvalue.annotation_id".format(res_table=res_table)
        results=search_omero_app.config["database_connector"].execute_query(sql)
        try:
            results=[res['name'] for res  in results]
            d = g.create_dataset(res_table, data=json.dumps(results))
        except Exception as e:
            search_omero_app.logger.info("Error while writing the file  ...."+ str(e))
            f.close()
            sys.exit(0)
    f.close()

def write_key_h5py(resource_table, keys):
    cached_folder = search_omero_app.config["CACHE_FOLDER"]
    cached_file_name = os.path.join(cached_folder, 'annotation_names.h5')
    f = h5py.File(cached_file_name, 'a')
    del_dataset = False
    try:
        g = f.create_group('keys')
    except Exception as e:
        search_omero_app.logger.info ("error Create group"+ str(e))
        del_dataset = True
        g = f['keys']

    if del_dataset:
        try:
            search_omero_app.logger.info ("{resource_table}".format(resource_table=resource_table))
            del f["keys"]["{resource_table}".format(resource_table=resource_table)]
        except  Exception as e:
            search_omero_app.logger.info ("Error delete dataset .."+str(e))

    try:
        d = g.create_dataset(resource_table, data=json.dumps(keys))
    except  Exception as e:
        search_omero_app.logger.info ("Error writing "+str(e))
        search_omero_app.logger.info (type(keys))
    f.close()


def write_key_values_h5py(resource_table, meta_values):
    cached_folder = search_omero_app.config["CACHE_FOLDER"]
    cached_file_name = os.path.join(cached_folder, 'metadata_h5py.h5')
    f= h5py.File(cached_file_name, 'a')
    del_dataset=False
    try:
        g = f.create_group('{table}'.format(table=resource_table))
    except:
        g=f['{table}'.format(table=resource_table)]
        del_dataset=True

    for key, values in meta_values.items():
        if not key:
            continue
        if del_dataset:
            try:
                del f['{table}/{key}'.format(table=resource_table, key=key)]
            except:
                pass
        try:
            d = g.create_dataset(key, data=json.dumps(values))
        except Exception as e:
            search_omero_app.logger.info ("Error while writing the file  ...."+ str(e))
            f.close()
            sys.exit(0)
    f.close()


def get_keys(res_table):
    sql = "select  distinct (name) from annotation_mapvalue inner join {res_table}annotationlink on {res_table}annotationlink.child=annotation_mapvalue.annotation_id".format(
        res_table=res_table)
    results= search_omero_app.config["database_connector"].execute_query(sql)
    results=[res['name'] for res  in results]
    return  results


def cached_values():
    '''
    cached the tables (e.g. image, project, ..) names and its related values to hd5 file
    '''
    for resource_table, linkedtable in annotation_resource_link.items():
        if resource_table!="image":
            continue

        search_omero_app.logger.info ("check table: %s ......."%resource_table)
        resource_keys =get_keys(resource_table)
        table_node=DataFrame()
        table_node['key']=resource_keys
        meta_values={}
        co=0
        for key in table_node['key']:
            if not key:
                continue
            org_key=key

            co += 1
            search_omero_app.logger.info("Check values for key %s" % key)
            search_omero_app.logger.info(str(co)+ "//"+ str(len(table_node['key'])))
            if "'" in key:
                key=key.replace("'","''")

            linked_table = annotation_resource_link[resource_table]
            sql_statment = "select distinct(annotation_mapvalue.value) from annotation_mapvalue  inner join {linked_table} on {linked_table}.child=annotation_mapvalue.annotation_id where annotation_mapvalue.name='{key}'".format(
                linked_table=linked_table, key=key)
            res = search_omero_app.config["database_connector"].execute_query(sql_statment)
            res_to_save=[rs['value'] for rs in res]
            if len(res_to_save)>0:
                meta_values[org_key]=res_to_save


        to_be_deleted=[]
        for key_, value in meta_values.items():
            to_be_deleted=[]
            for me_va in value:
                if not me_va:
                    to_be_deleted.append((me_va))
            for me_va in to_be_deleted:
                value.remove(me_va)

        if meta_values.values() and len(meta_values.values()) > 0:
            write_key_h5py(resource_table, list(meta_values.keys()))
            write_key_values_h5py(resource_table, meta_values)


def read_name_values_from_hdf5(resource_table, name):
    ''''
     read the value for a key for a resource table
    '''
    cached_folder = search_omero_app.config["CACHE_FOLDER"]
    cached_file_name = os.path.join(cached_folder, "metadata_h5py.h5")
    if not os.path.exists(cached_file_name):
        return  []

    f=h5py.File(cached_file_name, "r")
    try:
        metadata = json.loads(f["{resource_table}/{name_to_search}".format(resource_table=resource_table,name_to_search=name)][()])
        f.close()
        return metadata
    except Exception as e:
        search_omero_app.logger.info ("Error: "+str(e))
        f.close()
        return []



def delete_cacheded_key(resource_table, key, value=None):
    cached_folder = search_omero_app.config["cached_FOLDER"]
    cached_file_name = os.path.join(cached_folder, ".h5")
    f = h5py.File(cached_file_name, "a")
    main_node = "{table}".format(table=resource_table)
    try:
        if main_node in f.keys():
            g = f[main_node]
            if key in g.keys():
                if not value:
                    del g[key]
                    search_omero_app.logger.info("{key} has  been deleted".format(key=key))
                elif value in g[key]:
                    del g[key][value]
                    search_omero_app.logger.info("{key}/{value} has  been deleted".format(key=key, value=value))

    except Exception as e:
        search_omero_app.logger.info ("Error"+ str(e))
        pass

    f.close()


def check_cacheded_query(resource_table, name, value, operator=None):
    '''
    check if the key value is cached or not
    if it is cached it will return the values
    otherwise will return None
    '''
    cached_folder = search_omero_app.config["cached_FOLDER"]
    if not operator:
        file_name=get_file_name(resource_table, name)
    else:
        file_name = get_file_name(resource_table, name, operator)
    cached_file_name = os.path.join(cached_folder, file_name)
    results=None
    if not os.path.exists(cached_file_name):
        return results
    try:
        f= h5py.File(cached_file_name, "r")
        main_node = "{table}".format(table=resource_table)
        if not main_node in f.keys():
            return None
        else:
            g=f[main_node]
        if operator:
            _ndnode="{name}/{operator}/{value}".format (name=name, value=value.replace("/","__"), operator=operator)
        else:
            _ndnode="{name}/{value}".format (name=name, value=value.replace("/","__"))
        if not  _ndnode in g.keys():
            return None
        results=json.loads(f['{resource_table}/{name_to_search}'.format(resource_table=main_node,name_to_search=_ndnode)][()])
        f.close()
    except Exception as e:
        f.close()
        search_omero_app.logger.info ("Errors..."+str(e))
    return results

def cachede_query_results(resource_table, key_, results, operator):
    '''
    save the values inisde a hdf5 file
    the file name has this format: resouce_key_value
    and if operator is not it will be:
    resouce_key_value_not
    '''
    cached_folder = search_omero_app.config["cached_FOLDER"]
    name_values=key_.split("/")
    file_name = get_file_name(resource_table, name_values[0],operator)
    cached_file_name = os.path.join(cached_folder,file_name)
    f = h5py.File(cached_file_name, 'a')
    main_node='{table}'.format(table=resource_table)
    if not main_node in f.keys():
        g = f.create_group(main_node)
    else:
        g=f[main_node]
    _ndnode=key_
    if _ndnode in g.keys():
        del g[_ndnode]
    dd=json.dumps(results)
    try:
        d = g.create_dataset(_ndnode, data=dd)
    except Exception as e:
        search_omero_app.logger.info ("Error: "+ str(e))
    f.close()
