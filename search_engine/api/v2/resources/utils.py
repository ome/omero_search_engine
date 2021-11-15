
import os, sys
import json
from elasticsearch import Elasticsearch, helpers

from datetime import datetime
import time
from multiprocessing import Pool, Manager
main_dir = os.path.abspath(os.path.dirname(__file__))
mm=main_dir.replace("search_engine/api/v1/resources","")
sys.path.append(mm)

from search_engine import search_omero_app
from search_engine.cache_functions.hdf_cache_funs import read_cash_for_table, read_name_values_from_hdf5

'''
Elastic search query templates
Must ==> AND
must_not ==>  NOT
should ==>OR
'''

resource_elasticsearchindex={"project":"project_keyvalue_pair_metadata",
                             "screen":"screen_keyvalue_pair_metadata",
                             "plate":"plate_keyvalue_pair_metadata",
                             "well":"well_keyvalue_pair_metadata",
                             "image":"image_keyvalue_pair_metadata_new"
                             }

must_name_condition='''{"match": {"key_values.name.keyword":"%s"}}'''
must_value_condition='''{"match": {"key_values.value.keyvalue":"%s"}}'''
wildcard_value_condition='''{"wildcard": {"key_values.value.keyvalue":"%s"}}'''
must_value_condition_contains='''{"match": {"key_values.value.keyvalue":"%*s*"}}'''
range_value_condition='''{"range":{"key_values.value.keyvalue":{"%s":"%s"} }}'''



range_dict={
"gte":  ">=",#"Greater-than or equal to",
"lte" : "<=",#Less-than or equal to",
"gt" : ">",#,"Greater-than",
"lt" : "<"# "Less-than"
}



must_name_condition='''{"match": {"key_values.name.keyword":"%s"}}'''
must_value_condition='''{"match": {"key_values.value.keyvalue":"%s"}}'''


nested_query_template='''{"nested": {"path": "key_values", "query":{"bool": {"must":[%s ] }}}}'''

nested_query_template_must_not='''{"nested": {"path": "key_values", "query":{"bool": {"must_not":[%s ] }}}}'''

must_term='''"must" : [%s]''' #==>>equal term
must_not_term='''"must_not": [%s]''' #===>not equal
should_term='''"should": [%s],"minimum_should_match" : %s ,"boost" : 1.0'''  #==>or
query_template='''{"query": {"bool": {%s}}}'''


def elasticsearch_query_builder(and_filter, or_filters):
    global nested_query_template, must_term, must_not_term,should_term
    nested_must_part=[]
    nested_must_not_part = []
    should_part_list=[]
    if and_filter and len (and_filter) >0:
        for filter in and_filter:
            search_omero_app.logger.info("FILTER %s"% filter)
            try:
                key=filter["name"]
                value=filter["value"]
                operator=filter["operator"]
            except:
                return {"notice":"Each Filter needs to have, name, value and operator keywords."}
            search_omero_app.logger.info("%s %s %s"%(operator, key, value))
            _nested_must_part=[]
            if operator=="equals":
                _nested_must_part.append(must_name_condition % (key))
                _nested_must_part.append(must_value_condition % (value))
                nested_must_part.append(nested_query_template % (",".join(_nested_must_part)))
            if operator=="contains":
                value="*{value}*".format(value=value)
                _nested_must_part.append(must_name_condition % (key))
                _nested_must_part.append(wildcard_value_condition % (value))
                nested_must_part.append( nested_query_template % (",".join(_nested_must_part)))
            elif operator in ["not_equals", "not_contains"]:
                nested_must_part.append(nested_query_template % (must_name_condition % (key)))

                if operator=="not_contains":
                    value="*{value}*".format(value=value)
                    nested_must_not_part.append(nested_query_template % (wildcard_value_condition % (value)))
                else:
                    nested_must_not_part.append(nested_query_template % (must_value_condition % (value)))
            elif operator in ["lt","lte", "gt","gte"]:
                nested_must_part.append(nested_query_template % (must_name_condition % (key)))
                nested_must_part.append(nested_query_template % (range_value_condition%(operator, value)))
       #must_not_term
    if or_filters and len(or_filters) > 0:
        added_keys=[]

        for or_filter in or_filters:
            should_values=[]
            shoud_not_value=[]
            should_names=[]
            key=or_filter["name"]
            value = or_filter["value"]
            operator=or_filter["operator"]
            if key not in added_keys:
                added_keys.append(key)
            should_names.append(must_name_condition % key)
            if operator=="equals":
                should_values.append(must_value_condition % value)
            elif operator == "contains":
                value = "*{value}*".format(value=value)
                should_values.append(wildcard_value_condition % (value))
            elif operator in ["not_equals", "not_contains"]:
                if operator == "not_contains":
                    value = "*{value}*".format(value=value)
                    shoud_not_value.append(wildcard_value_condition % (value))
                else:
                    shoud_not_value.append(must_value_condition % (value))
            elif operator in ["lt", "lte", "gt", "gte"]:
                should_values.append(range_value_condition % (operator, value))
                must_value_condition

            ss=",".join(should_names)
            ff= nested_query_template % ss
            should_part_list.append(ff)
            ss = ",".join(should_values)
            ff = nested_query_template % ss
            should_part_list.append(ff)
            if len(shoud_not_value)>0:
                ss = ",".join(shoud_not_value)
                ff = nested_query_template_must_not % ss
                should_part_list.append(ff)

    all_terms=""

    if len(nested_must_part)>0:
        nested_must_part_ =",".join(nested_must_part)
        nested_must_part_ = must_term % (nested_must_part_)

        if all_terms:
            all_terms=all_terms+","+nested_must_part_
        else:
            all_terms =nested_must_part_

    if len(nested_must_not_part) > 0:

        nested_must_not_part_=",".join(nested_must_not_part)
        nested_must_not_part_ = must_not_term % (nested_must_not_part_)

        if all_terms:
            all_terms = all_terms + "," + nested_must_not_part_
        else:
            all_terms = nested_must_not_part_

    if len(should_part_list) > 0:
        minimum_should_match=int(len(should_part_list)/2+1)
        should_part_ = ",".join(should_part_list)
        should_part_ = should_term % (should_part_, minimum_should_match)

        if all_terms:
            all_terms+=","+should_part_
        else:
            all_terms=should_part_

    return query_template %(all_terms)

def check_filters(res_table, filters):
    names=read_cash_for_table(res_table)
    search_omero_app.logger.info (str(filters))
    for filter_ in filters:
        if not filter_:
            continue
        for filter in filter_:
            key=filter["name"]
            value=filter["value"]
            if key not in names:
                search_omero_app.logger.info ("Name Error %s"% str(key))
            values=read_name_values_from_hdf5(res_table, key)
            if value not in values:
                search_omero_app.logger.info ("Value Error: %s/%s"%(str(key),str(value)))

def search_index_scrol(index_name, query):
    results=[]
    es=search_omero_app.config.get("es_connector")
    try:
        res = helpers.scan(
        client=es,
        scroll='1m',
        query=query,
        index=index_name)
    except Exception as ex:
        search_omero_app.logger.info (str(ex))
        return results

    search_omero_app.logger.info ("Results: %s"% res)
    counter=0
    for i in res:
        counter+=1
        results.append(i)
    search_omero_app.logger.info ("Total =%s"% counter)
    return results


def search_index_using_seargc_after(e_index, query, page, bookmark_):
    returned_results = []
    if not page:
        page=1
    page_size=search_omero_app.config.get("PAGE_SIZE")
    es=search_omero_app.config.get("es_connector")
    start__= datetime.now()
    res = es.count(index=e_index, body= query)
    size = res['count']
    search_omero_app.logger.info ("Total: %s"% size)
    query['size']=page_size
    if size % page_size == 0:
        add_to_page=0
    else:
        add_to_page=1
    no_of_pages= (int) (size/page_size) +add_to_page
    search_omero_app.logger.info("==>>%s"%no_of_pages)
    query["sort"]= [
        {"id": "asc"}
    ]
    if not bookmark_:
        result = es.search(index=e_index, body= query)
        if len(result['hits']['hits'])==0:
            search_omero_app.logger.info ("No result is found")
            return returned_results
        bookmark = [result['hits']['hits'][-1]['sort'][0]]
        search_omero_app.logger.info ("bookmark: %s"%bookmark)
        for hit in result['hits']['hits']:
            #print (hit)
            returned_results.append(hit["_source"])
    else:
        search_omero_app.logger.info (bookmark_)
        query["search_after"]= bookmark_
        res = es.search(index=e_index, body=query)
        for el in res['hits']['hits']:
            returned_results.append(el["_source"])
        bookmark = [res['hits']['hits'][-1]['sort'][0]]
        page+=1
    return {"results" : returned_results, "total_pages":no_of_pages,"bookmark":bookmark, "size":size,"page":page}


def search_resource_annotation(table_, query, page=None,bookmark=None):
    '''
    @table_: the resource table, e.g. image. project, etc.
    @query: the a dict contains the three filters (or, and and  not) items
    '''
    res_index=resource_elasticsearchindex.get(table_)
    if not res_index:
        return {"error":"{table_} is not valid resurces is provided".format(table_)}

    start_time = time.time()
    query_details = query.get('query_details')

    if not query or len(query) == 0:
        return ""
    and_filters = query_details.get("and_filters")
    or_filters = query_details.get("or_filters")
    check_filters(table_, [and_filters, or_filters])
    query_string = elasticsearch_query_builder(and_filters,  or_filters)
    if isinstance(query_string, dict):
        return query_string

    search_omero_app.logger.info("Query %s"%query_string)

    query = json.loads(query_string)
    res=search_index_using_seargc_after(res_index, query, page, bookmark)
    notice=""
    end_time = time.time()
    query_time = ("%.2f" % (end_time - start_time))
    return {"results": res, "query_details": query_details, "resource": table_,
            "server_query_time": query_time, "notice": notice}



