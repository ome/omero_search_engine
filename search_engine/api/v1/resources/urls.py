from . import resources
from flask import request, jsonify
import json
from search_engine.api.v1.resources.utils import search_resource_annotation, get_annotation_keys, get_resource_annotation_table
from search_engine.cache_functions.hdf_cache_funs import read_name_values_from_hdf5,get_resource_names


@resources.route('/',methods=['GET','POST'])
def index():
    return "Omero search engine (API V1)'\'"


@resources.route('/<resource_table>/searchannotation/',methods=['GET','POST'])
def search_resource(resource_table):
    '''
       ApI end point to search the annotation (key/value pair) for a resource (resource table, e.g. image, project, study, ..)
       the request data contation a dict (query) which contains the the query detatins
       an example of a query dict i:

       q_data={"query":{'query_details':{"and_filters":and_filters, "not_filters": not_filters,"or_filters":or_filters}}}
       each of and_filters, or_filters and not_filters is a list of dict whihc contains the search conditions, an example of and_filters is:
       and_filters=[{"Organism" : "Homo sapiens"},{"Gene Symbol": "NCAPD2"},{ "Cell Cycle Phase" :"anaphase"}]
       and_filters means that the results have to saitisy the conditions
       not_filters means that the results have not to the conditions
       or_filters means that the results should satsify at least one condition inside the filters
     '''

    if not (get_resource_annotation_table):
        return ("NO data for table {table}".format(table=resource_table))
    data = request.data
    if not data:
        return "Error: {error}".format(error="No query data is provided ")
    try:
        data = json.loads(data)
    except Exception as ex:
        return "Error: {error}".format(error="No proper query data is provided ")

    if 'query' in data:
        query = data['query']
        from search_engine import search_omero_app
        #check if the app configuration will use ASYNCHRONOUS SEARCH or not.
        if search_omero_app.config.get("ASYNCHRONOUS_SEARCH"):
            resource_list = search_resource_annotation.apply_async( kwargs={"table_":resource_table, "query":query})
            return jsonify({"task_id":  resource_list.id})
        else:
            resource_list = search_resource_annotation(resource_table, query)
    else:

        return "Error: No query field is provided. please specify an id."
    return jsonify(resource_list)

@resources.route('/<resource_table>/getannotationkeys/',methods=['GET','POST'])
def get_resource_keys(resource_table):
    '''
    return the keys for a resource
    '''
    if not (get_resource_annotation_table(resource_table)):
        return ("NO data for table {table}".format(table=resource_table))
    resource_keys=get_annotation_keys(resource_table)
    return jsonify (resource_keys)

@resources.route('/<resource_table>/getannotationvalueskey/',methods=['GET','POST'])
def get_resource_key_value(resource_table):
    '''
    get the values for a key for a specific resource
    '''
    if not (get_resource_annotation_table(resource_table)):
        return ("NO data for table {table}".format(table=resource_table))
    key=request.args.get("key")
    if not key:
        return jsonify ("No key is provided")
    resource_keys=read_name_values_from_hdf5(resource_table, key)
    return jsonify (resource_keys)


@resources.route('/<resource_table>/getresourcenames/',methods=['GET','POST'])
def get_resource_names_(resource_table):
    '''
    get the values for a key for a specific resource
    '''
    if not (get_resource_annotation_table(resource_table)):
        return ("NO data for table {table}".format(table=resource_table))


    names=get_resource_names(resource_table)
    return jsonify (names)