import os
import json
from search_engine import search_omero_app, create_app
from flask_script import Manager
from flask import jsonify
manager = Manager(search_omero_app)
#create_app()

from search_engine.cache_functions.cache_funs import update_cash, cash_values,  delete_cashed_key, check_cashed_query

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
def set_cash_pandas_hdf5():
    ''''
    cahnames and values for each resource (e.ge image, project, ..
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


if __name__ == '__main__':
    manager.run()