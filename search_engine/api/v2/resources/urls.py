from . import resources
from flask import request, jsonify
import json
from search_engine.api.v2.resources.utils import search_resource_annotation, build_error_message
from search_engine.api.v1.resources.utils import get_resource_annotation_table

@resources.route('/',methods=['GET'])
def index():
    return "Omero search engine (API V2)  '\'"

@resources.route('/<resource_table>/searchannotation_page/',methods=['GET'])
def search_resource_page(resource_table):
    '''
    used to get the next results page
    '''
    if not (get_resource_annotation_table):
        return jsonify (build_error_message("No data for table {table}".format(table=resource_table)))
    data = request.data
    if not data:
        return jsonify(build_error_message("Error: {error}".format(error="No query data is provided ")))
    try:
        data = json.loads(data)
    except Exception as ex:
        return jsonify(build_error_message("{error}".format(error="No proper query data is provided ")))

    if 'query' in data:
        query = data["query"]
        page=data.get("page")
        bookmark=data.get("bookmark")
        from search_engine import search_omero_app
        resource_list = search_resource_annotation(resource_table, query, page=page,bookmark=bookmark)
    else:

        return jsonify(build_error_message("Error: No query field is provided. please specify an id."))
    return jsonify(resource_list)


@resources.route('/<resource_table>/searchannotation/',methods=['GET'])
def search_resource(resource_table):
    '''
       API end point to search the annotation (key/value pair) for a resource (resource table, e.g. image, project, study, ..)
       the request data contation a dict (query) which contains the the query detatins.
       Version 2 uses Elastic search
       an example of a query dict i:

       q_data={"query":{'query_details':{"and_filters":and_filters,"or_filters":or_filters}}}
       each of and_filtersand or_filters is a list of dict whihc contains the search conditions, an example of and_filters is:
       and_filters=[{"Organism" : "Homo sapiens", "operator": "equals"},{"Gene Symbol": "NCAPD2", "operator": "equals"},{ "Cell Cycle Phase" :"anaphase", "operator": "equals"}]
       and_filters means that the results have to saitisy the conditions
       not_filters means that the results have not to the conditions
       or_filters means that the results should satsify at least one condition inside the filters
     '''
    if not (get_resource_annotation_table):
        return jsonify({"notice":"NO data for table {table}".format(table=resource_table)})
    data = request.data
    if not data:
        return jsonify(build_error_message("Error: {error}".format(error="No query data is provided ")))
    try:
        data = json.loads(data)
    except Exception as ex:
        return jsonify(build_error_message("Error: {error}".format(error="No proper query data is provided ")))

    if 'query' in data:
        query = data['query']
        #check if the app configuration will use ASYNCHRONOUS SEARCH or not.
        resource_list = search_resource_annotation(resource_table, query)
    else:
        return jsonify(build_error_message("Error: No query field is provided. please specify an id."))

    return jsonify(resource_list)