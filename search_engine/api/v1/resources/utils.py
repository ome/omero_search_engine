
import os, sys
from datetime import datetime
import time
from multiprocessing import Pool, Manager
main_dir = os.path.abspath(os.path.dirname(__file__))
mm=main_dir.replace("search_engine/api/v1/resources","")
sys.path.append(mm)

from search_engine import search_omero_app, make_celery
from app_data.data_attrs import annotation_resource_link
from search_engine.cache_functions.hdf_cache_funs import read_cash_for_table, cashe_query_results, check_cashed_query,read_name_values_from_hdf5
annotation_mapvalue="annotation_mapvalue"

celery = make_celery(search_omero_app)
tables=["project","image","dataset","plate"]

sql_="select  il.parent  from imageannotationlink as il inner join annotation_mapvalue as map_1 on map_1.annotation_id=il.child  where (map_1.name='Organism' and  map_1.value= 'Homo sapiens') and  il.parent in (select il2.parent from  imageannotationlink as il2 inner join annotation_mapvalue as map_2 on map_2.annotation_id=il2.child where (map_2.name='Cell Line' and  map_2.value= 'HeLa'))"

def get_names(sent_names, db_names):
    suggested_names={}
    for sent_name in sent_names:
        for db_name in db_names:
            if sent_name.lower() in db_name.lower():
                suggested_names[sent_name]=db_name
    return suggested_names

def get_resource_annotation_table(resource_table):
    '''
    return the related annotation for the resources table
    it can use annotation_resource_link dict
    '''
    if resource_table in annotation_resource_link:
        return annotation_resource_link[resource_table]
    elif resource_table.lower()=="all":
        return  annotation_resource_link
    else:
        return None

def test_names(table, meta_data):
    table_names_cash_data=read_cash_for_table(table)
    for name, value in meta_data.items():
        if name not in table_names_cash_data:
            suggested_names=test_names(name,table_names_cash_data)
            raise Exception(
                "The provided name: {name} is not found in the annotation for {table}s".format(name=name, table=table_names_cash_data))
    return table_names_cash_data

def build_sql_statment(table, filters, cashed_values, operator="="):
    '''
      Build sql statment using the table name and filters inside the meta_data_dict
    '''
    cashed_results=[]
    sqls={}
    if table=='study':
        table='screen'
    linked_table=get_resource_annotation_table(table)
    if not linked_table:
        raise Exception ("No annotation linked table is avilable for table %s"%table)

    # base sql which is used to build the returned sql statment
    search_omero_app.logger.info("Build sql statments ")
    sql_ = "select parent as id , {table}.name as name from {linked_table} inner join annotation_mapvalue on {linked_table}.child=annotation_mapvalue.annotation_id inner join {table} on {table}.id={linked_table}.parent where".format(
        linked_table=linked_table, table=table)

    for filter in filters:
        search_omero_app.logger.info ("Filter {ff}".format(ff=filter))
        for name, value in filter.items():
            search_omero_app.logger.info("name {name}".format(name=name))
            search_omero_app.logger.info("value {value}".format(value=value))
            #print ("Start Date: ", datetime.now())
            #print ("Start Date: ", datetime.now())
            ##########should be used to read all cashed values on one go
            #if operator=="!=":
            #    _ndnode = "{name}/not/{value}".format(name=name, value=value)
            #else:
            #    _ndnode = "{name}/{value}".format(name=name, value=value)

            #val=cashed_values.get(_ndnode)


            ###########
            if operator!="=":
                val=check_cashed_query (table, name, value,operator="not")
            else:
                val = check_cashed_query(table, name, value)
            #check if  the item is saved inside the cached file
            if val and len(val)>0:
                val_=val
                cashed_results.append(val_)
                search_omero_app.logger.info ("Cashed Value for '{name}'/'{value}' is {len}".format(name=name, value=value,len=len(val)))
                continue

            if "'" in name:
                name_ = name.replace("'", "''")
            else:
                name_ = name

            sql = sql_ + " annotation_mapvalue.name='{name}' and annotation_mapvalue.value {filter} '{value}' ".format(
                    filter=operator, name=name_,
                    value=value)

            sqls["{name}/{value}".format(name=name_, value=value.replace("/","__"))]=sql
    search_omero_app.logger.info ("Query: "+str(len(sqls))+", cashed: "+str(len(cashed_results)))
    return sqls, cashed_results


def search_studies(query):
    {'Study Title':'Comparative RNAi screening identifies a conserved core metazoan actinome by phenotype'}
    meta_data = query.get('meta_data')
    operators = query.get('operators')
    if not operators:
        operators='or'
    table_names_cash_data=test_names('screen',meta_data)


def run_sql_statment(sql_statment):
    res = search_omero_app.config["database_connector"].execute_query(sql_statment)
    return res


def run_sql_statments(sql_statments):
    results=[]
    count=0
    search_omero_app.logger.info("Running sql statments ")
    for sql in sql_statments:
        search_omero_app.logger.info(str(count+1)+ "/"+ str(len(sql_statments)))
        search_omero_app.logger.info (sql)
        res=run_sql_statment(sql)
        results.append(res)
        count+=1
    return results

def get_tables(names):
    table_to_search={}
    cashed_tables_names=read_cash_for_table(tables=tables)
    for table, existing_names in cashed_tables_names.items():
        for name in names:
            if name in existing_names:
                if table not in table_to_search:
                    table_to_search[table]=[name]
                else:
                    table_to_search.get(table).append(name)
    return table_to_search


def run_filter(sql_statments, included_):
    search_omero_app.logger.info (str(type(included_)))
    results = run_sql_statments(sql_statments)
    returned_results = {}
    for res in results:
        returned_results={str(ss['id']): {"name": ss["name"]} for ss in res}
    included_[sql_statments[0]]=returned_results

def check_filters(res_table, filters):
    names=read_cash_for_table(res_table)
    search_omero_app.logger.info (str(filters))
    for filter_ in filters:
        for filter in filter_:
            for key, value in filter.items():
                if key not in names:
                    search_omero_app.logger.info ("Name Error "+ str(key))
                values=read_name_values_from_hdf5(res_table, key)
                if value not in values:
                    search_omero_app.logger.info ("Value Error: "+str(value))

def add_query_results(table, sqls_dict, sql, results, operator=None):
    for key, sql_ in sqls_dict.items():
        if sql==sql_:
            if operator:
                key=key.replace("/","/{operator}/".format(operator=operator))

            cashe_query_results(table, key, results,operator)

def get_dict_intersection(dict1, dict2):
    shared_keys = dict1.keys() & dict2.keys()
    shared_dict = {k: dict1[k] | dict2[k] for k in shared_keys}
    return shared_dict

@celery.task
def search_resource_annotation(table_, query, get_addition_results=False):
    '''
    It will seacrg Omero database using three differnt of fillters. i.e. and, or and not
    for each condition in  searach criteria, it will first search the cached results, and if find item is cached it will use it
    otherwise it will create a sqm stament and query the database and after that it will save the results in the cache file,
    so it will be available in case if it is included in other query
    if the item is

    @table_: the resource table, e.g. image. project, etc.
    @query: the a dict contains the three filters (or, and and  not) items
    '''
    start_time=time.time()
    tables=[table_]
    query_details=query.get('query_details')

    if not query or len(query)==0:
        return ""
    and_filters=query_details.get("and_filters")
    or_filters=query_details.get("or_filters")
    not_filter=query_details.get("not_filters")
    have_been_cashed ={}
    check_filters(table_,[and_filters, or_filters, not_filter])
    #it support using all keyword to search all the database
    #it has been tested for simple examples, it needs more work for verfication
    #so I will disable it for the moment
    if table_ == 'all':
        raise Exception("No valid table name is provided")
        tables_to_search = {}
        names=[]
        if and_filters:
            for name in and_filters:
                names.append(name)
        if or_filters:
            for name in or_filters:
                names.append(name)
        if not_filter:
            for name in not_filter:
                names.append(name)
        if len(names)>0:
            tables_to_search=get_tables(names)
            tables=tables_to_search.keys()
        else:
            raise Exception("No valid name is provided")

    rest_results={}
    #a list contains all the sql statments for and and not conditions.
    sql_statments=[]
    # a list contains all the sql statments for or condition.
    or_sql_statments = []
    #dict to stor the cached results
    cashed_results={}
    #dicts contain the results from quering the database
    sqls_or={}
    sqls_not={}
    sqls_and = {}
    try:
        for table in tables:
            cashed_values={}
            search_omero_app.logger.info("Checking the {table} resource ...".format(table=table))
            if not_filter and len (not_filter)>0:
                sqls_not, cashed_results_=build_sql_statment(table, not_filter, cashed_values, operator="!=")
                if len(cashed_results_)>0:
                    cashed_results["not"]=cashed_results_

                if sqls_not and len(sqls_not)>0:
                     sql_statments=sql_statments+list(sqls_not.values())
            if or_filters and len(or_filters)>0:
                #if table=="all":
                #    for name, table in tables_to_search.items():
                #        sqls_or = build_sql_statment(table, names)
                #else:
                sqls_or, cashed_results_ = build_sql_statment(table, or_filters,cashed_values)

                if sqls_or and len (sqls_or)>0:
                    #or_sql_statments=sql_statments+list(sqls_or.values())
                    or_sql_statments = list(sqls_or.values())
                if len(cashed_results_)>0:
                    cashed_results["or"]=cashed_results_

            if and_filters and len(and_filters)>0:
                sqls_and, cashed_results_ = build_sql_statment(table, and_filters, cashed_values)
                if sqls_and and len(sqls_and)>0:
                    sql_statments=sql_statments+list(sqls_and.values())
                if len(cashed_results_)>0:
                    cashed_results['and']=cashed_results_
            #When not using celey (by setting "ASYNCHRONOUS_SEARCH" to False inside the app configuration file
            #Then it will use paralle search, this should use carfully as it will raise erro in case of two process trying to updatethe hdf5 file at the same time.
            #Anyway we should have a mchanism to lock the file for writing when another process updating it.
            no_quries=len(or_sql_statments)+len(sql_statments)
            if not search_omero_app.config.get("ASYNCHRONOUS_SEARCH") and no_quries>0:
                manager = Manager()
                return_dict = manager.dict()
                pool = Pool(processes=no_quries)
                for sql in sql_statments:
                    pool.apply_async(run_filter, [[sql], return_dict])
                for sql in or_sql_statments:
                    pool.apply_async(run_filter, [[sql], return_dict])
                pool.close()
                pool.join()
            else:
                #This used by celery
                return_dict={}
                or_return_dict = {}
                for sql in sql_statments:
                    search_omero_app.logger.info ("Going to run: "+ sql)
                    run_filter ([sql], return_dict)
                for sql in or_sql_statments:
                    search_omero_app.logger.info ("Going to run "+ sql)
                    run_filter ([sql], or_return_dict)
            returned_results={}
            counter_=0
            or_results={}
            to_be_ignored=[]
            cash_or_results= {}
            if len(or_sql_statments)>0:
                for sql__ in or_sql_statments:
                    if sql__ in or_return_dict:
                        cash_or_results={** cash_or_results,**or_return_dict[sql__]}
                        to_be_ignored.append(sql__)
            search_omero_app.logger.info ("1. Or Cash "+str(len(cash_or_results)))

            if "or" in cashed_results:
                for v in cashed_results["or"]:
                    cash_or_results = {**cash_or_results, **v}

            for k, v in or_return_dict.items():
                add_query_results(table, sqls_or, k, v)


            for k,v in return_dict.items():
                #cahs the sql statments results, if there any
                add_query_results(table, sqls_and, k, v)
                search_omero_app.logger.info ("cache or ..........")
                add_query_results(table, sqls_or, k, v)
                search_omero_app.logger.info("end Cache or ..........")
                add_query_results(table, sqls_not, k, v, operator="not")

                if k in to_be_ignored:
                    continue

                if counter_==0:
                    returned_results=v
                else:
                    returned_results=get_dict_intersection(returned_results,v)
                counter_+=1
            for k, val_ in cashed_results.items():
                #escape the or condition as it will be used later
                if k=="or":
                    continue

                if k in to_be_ignored:
                    continue
                for v in val_:
                    if counter_ == 0:
                        returned_results = v
                    else:
                        returned_results = get_dict_intersection(returned_results, v)

                    search_omero_app.logger.info ("Cache: "+str(len(returned_results)))
                    counter_ += 1
            if len(cash_or_results)>0:
                if counter_==0:
                    returned_results=cash_or_results
                else:
                    returned_results = get_dict_intersection(returned_results, cash_or_results)
                counter_ += 1
                        #sss= list(set(sss) & set(cash_or_results))
            max_size=search_omero_app.config["MAX_RETUNED_ITEMS"]
            coo=0
            notice="None"
            if len (returned_results)>max_size:
                notice="The query results are {items} records. A maximum of {max_size} records are displayed for performance resaons".format(items=len(returned_results), max_size=max_size)
                kk=list(returned_results.keys())
                returned_results_={ kk[i]:returned_results[kk[i]] for i in range (max_size)}
            else:
                returned_results_=returned_results

            end_time = time.time()
            query_time = ("%.2f" % (end_time - start_time))

            search_omero_app.logger.info("Query time: " + str(query_time))

            return {"results":returned_results_, "query_details":query_details, "resource": table, "server_query_time": query_time, "notice":notice}

    except Exception as ex:
        search_omero_app.logger.info("Error: ", str(ex))
        search_omero_app.logger.info("query_details: ",str(query_details))
        end_time = time.time()
        query_time = end_time - start_time

        return {"Error_message": str(ex),"query_details":query_details, "resource": table, "server_query_time": query_time}
        # the following code can be used to add more to the returned results
        #but it will increase the query time and the app respond
        #We can add a flag to the request for using the code in case of the user needs more results rather thna image name and id
        if len(returned_results)>0:
            res= get_resource_meta_data(table, returned_results, get_addition_results)
            rest_results[table]=res
    return rest_results



def get_resource_(table, query):
    meta_data=query.get('meta_data')
    meta_data =query

    if not meta_data or len(meta_data)==0:
        return ""
    filters=query.get('filters')

    if not filters or len(filters)==0:
        operators='or'
    sql=build_sql_statment(table, meta_data, operators)
    ids=search_omero_app.config["database_connector"].execute_query(sql)
    if len(ids)>0:
        return (get_resource_meta_data(table,ids))
    return ids

def get_images_dataset_project(ids):
    sql="select project.name as project_name,project.id as project_id, dataset.name as dataset_name, dataset.id as dataset_id, datasetimagelink.child as image_id from projectdatasetlink inner join" \
        " dataset on dataset.id=projectdatasetlink.child inner join project on project.id=projectdatasetlink.parent inner join" \
        " datasetimagelink on datasetimagelink.parent=dataset.id where project.id is not null and dataset.id is not null and datasetimagelink.child in ({ids})".format(ids=ids)
    results = search_omero_app.config["database_connector"].execute_query(sql)
    return  results

def get_images_plates_screens(ids):
    sql="select wellsample.image as image_id, screenplatelink.parent as screen_id, screen.name as screen_name , plate.name as plate_name, plate.id as plate_id from plate inner join screenplatelink on screenplatelink.child=plate.id inner join  well on well.plate=plate.id inner join wellsample on wellsample.well=well.id inner join screen on screen.id=screenplatelink.parent where wellsample.image in ({ids})".format(ids=ids)
    results= search_omero_app.config["database_connector"].execute_query(sql)
    screens=[]
    plates=[]
    for res in results:
        if res.get("screen_id") not in screens:
            screens.append(res.get("screen_id"))
        if res.get("plate_id") not in plates:
            plates.append(res.get("plate_id"))
    return results


def get_resource_meta_data(table,ids_, get_additional_results=False):
    org_table=table
    if table=='study':
        table='screen'
    ids__=ids_#[len(ids_)-100: ]
    ids = ','.join(str(x) for x in ids__)
    search_omero_app.logger.info (table)
    sql="select id as {table}_id , name as {table}_name from {table} where id in ({ids})".format(table=table, ids=ids)
    ###needs to be optimized
    if get_additional_results:
         sql_="select {table}.id as {table}_id, {table}.name {table}_name, annotation_mapvalue.name as annotation_name, annotation_mapvalue.value as annotation_value from {table} inner join {table}annotationlink on {table}annotationlink.parent={table}.id inner join annotation_mapvalue on annotation_mapvalue.annotation_id={table}annotationlink.child where {table}annotationlink.parent in ({ids})".format(ids=ids,table=table)
    else:
         sql_ = "select {table}.id as {table}_id, {table}.name {table}_name from {table} join {table}annotationlink on {table}annotationlink.child=annotation_mapvalue.annotation_id inner join {table} on {table}.id={table}annotationlink.parent where {table}annotationlink.parent in ({ids})".format(
        ids=ids, table=table)
    start_=datetime.now()
    results =search_omero_app.config["database_connector"].execute_query(sql)
    end_ = datetime.now()
    search_omero_app.logger.info (str(start_)+str(end_))
    main_key = "{table}_id".format(table=table)
    final={}
    for res in results:
        if res.get(main_key) in final:
            dict_=final[res.get(main_key)]
        else:
            dict_={}
            dict_[main_key] = res.get(main_key)
            final[res.get(main_key)]=dict_
        if res.get('annotation_name') and res.get('annotation_value'):
            dict_[res.get('annotation_name')]=res.get('annotation_value')
        for key, value in res.items():
            if key in (main_key, 'annotation_value','annotation_value'):
                continue
            dict_[key]=value
    return final

    if org_table=='image':
        addition_info=get_images_plates_screens(ids)
        project_dataset_info=get_images_dataset_project(ids)
        for info in addition_info:
            if info.get(main_key):
                kk=info.get(main_key)
                dict_=final.get(kk)
                if dict_:
                    dict_['screen_name']=info.get('screen_name')
                    dict_['screen_id'] = info.get('screen_id')
                    dict_['plate_name'] = info.get('plate_name')
                    dict_['plate_id'] = info.get('plate_id')
        for p_infor in project_dataset_info:
            if p_infor.get(main_key):
                kk=p_infor.get(main_key)
                dict_=final.get(kk)
                if dict_:
                    dict_['project_name'] = p_infor.get('project_name')
                    dict_['project_id'] = p_infor.get('project_id')
                    dict_['dataset_name'] = p_infor.get('dataset_name')
                    dict_['dataset_id'] = p_infor.get('dataset_id')
    elif org_table=='study':
        for info_ in final:
            pass

    return final


def get_annotation_keys(table):
    if table=='study':
        table='screen'
    linked_table = get_resource_annotation_table(table)
    if not linked_table:
        return("No annotation linked table is avilable for table %s" % table)
    if isinstance(linked_table,str):
        resource_keys = read_cash_for_table(table)
        return resource_keys
    elif isinstance(linked_table, dict):
        returned_keys={}
        for table_, linkedtable in linked_table.items():
            resource_keys = read_cash_for_table(table_)
            returned_keys[table_]=resource_keys
        return returned_keys

