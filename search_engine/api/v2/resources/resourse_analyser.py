from string import Template
from search_engine import search_omero_app
from datetime import datetime
import time
from utils import resource_elasticsearchindex

key_number_search_template=Template('''{"size":0,"aggs":{"value_search":{"nested":{"path":"key_values"},
         "aggs":{"value_filter":{"filter":{"terms":{"key_values.name.keyword":["$key"]}},
               "aggs":{"required_values":{"cardinality":{"field":"key_values.value.keyvalue","precision_threshold":100
                     }}}}}}}}
                     ''')

search_bey_value_only= Template('''
                    {"query":{"bool":{"must":[{"nested":{"path":"key_values","query":{"bool":{"must":[{"wildcard":
                                                        {"key_values.value.keyvaluenormalize":"*eLa*"}}]}}}}]}}}
                         ''')
'''
The number of returned value is limited to 9999
I will add paging to these statment to pull all the results
'''
value_number_search_template = Template('''
            {"size": 0,"aggs": {"name_search": {"nested": {"path": "key_values"},"aggs": {"value_filter": {"filter": {
                "terms": {"key_values.value.keyvaluenormalize": ["$value"]}},"aggs": {"required_name": {"cardinality": {
                    "field": "key_values.name.keyword","precision_threshold": 100}}}}}}}}
                    ''')

value_search_template=Template('''{"size": 0,"aggs": {"name_search": {"nested": {"path": "key_values"},"aggs": {"value_filter": {
          "filter": {"terms": {"key_values.value.keyvaluenormalize": ["$value"]}},"aggs": {"required_name": {
              "terms": {"field": "key_values.name.keyword","size": 9999}}}}}}}}
              ''')

value_search_contain_template = Template('''{"size": 0,"aggs": {"name_search": {"nested": {"path": "key_values"},
          "aggs": {"value_filter": {"terms": {"field":"key_values.value.keyvaluenormalize","include": ".*$value.*"
              },"aggs": {"required_name": {"terms": {"field": "key_values.name.keyword","size": 9999}}}}}}}}
    ''')

key_search_template=Template('''{"size": 0,"aggs": {"name_search": {"nested": {"path": "key_values"},"aggs": {"value_filter": {
          "filter": {"terms": {"key_values.name.keyword": ["$key"]}},"aggs": {"required_values": {
              "terms": {"field": "key_values.value.keyvalue","size": 9999}}}}}}}}
              ''')


def format_the_results(results):
    pass

def search_index_for_value(e_index, query):
    '''
    Perform search the elastcisearch using value and return all the key values whihch this value has been used, it will include thenumber of records
    It relatively slow but I think it may be my the elasticsearcg hsting  machine
    '''

    es = search_omero_app.config.get("es_connector")
    res = es.search(index=e_index, body=query)
    return res


def search_value_for_resource(table_, value):
    '''
    send the request to elasticsearch and format the results
    '''
    start_time = time.time()
    res_index = resource_elasticsearchindex.get(table_)
    query=value_search_contain_template.substitute(value= value.lower())
    res = search_index_for_value(res_index, query)
    end_time = time.time()
    query_time = ("%.2f" % (end_time - start_time))
    notice = ""
    #print("TIME ...", query_time)
    total_number=0
    returnted_results=[]
    if res.get("aggregations"):
        for bucket in res.get("aggregations").get("name_search").get("value_filter").get("buckets"):
            value=bucket.get("key")
            value_no=bucket.get("doc_count")
            for buc in bucket.get("required_name").get("buckets"):
                singe_row = {}
                returnted_results.append((singe_row))
                key = buc.get("key")
                key_no = buc.get("doc_count")
                singe_row["Attribute"]=key
                singe_row["Value"] =value
                singe_row["Number of %ss"%table_] =key_no
                total_number+=key_no
    return {"returnted_results":returnted_results, "total_number":total_number}

def get_number_of_buckets(key, res_index):
    query=key_number_search_template.substitute(key=key)
    res = search_index_for_value(res_index, query)
    number_of_buckets = res.get("aggregations").get("value_search").get("value_filter").get("required_values").get(
        "value")
    number_of_images = res.get("aggregations").get("value_search").get("value_filter").get("doc_count")
    #print (number_of_buckets, number_of_images)
    return number_of_buckets, number_of_images



def get_values_for_a_key(table_, key):
    '''
    search the index to get he avialble values for a key and get values number for the key
    '''
    total_number=0
    res_index = resource_elasticsearchindex.get(table_)
    number_of_buckets, number_of_images=get_number_of_buckets(key, res_index)
    query=key_search_template.substitute(key=key)
    start_time = time.time()
    res = search_index_for_value(res_index, query)
    query_time = ("%.2f" % (time.time() - start_time))
    #print("TIME ...", query_time)
    returnted_results=[]
    if res.get("aggregations"):
        for bucket in res.get("aggregations").get("name_search").get("value_filter").get("required_values").get("buckets"):
            value = bucket.get("key")
            value_no = bucket.get("doc_count")
            total_number+=value_no
            singe_row = {}
            returnted_results.append(singe_row)
            singe_row["Attribute"] = key
            singe_row["Value"] = value
            singe_row["Number of %ss"%table_] = value_no
    return {"returnted_results":returnted_results, "total_number":total_number, "total_number_of_images":number_of_images,"total_number_of_buckets": number_of_buckets}



def get_keys_for_value(table, key):
    pass

