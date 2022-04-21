from . import resources
from flask import request, jsonify
import json
from search_engine.api.v1.resources.utils import search_resource_annotation, build_error_message
from search_engine.api.v1.resources.resourse_analyser import  search_value_for_resource,query_cashed_bucket, get_resource_attributes, get_resource_attribute_values, get_resource_names, get_values_for_a_key, query_cashed_bucket_value
from search_engine.api.v1.resources.utils import get_resource_annotation_table

@resources.route('/',methods=['GET'])
def index():
    return "Omero search engine (API V1)"

@resources.route('/<resource_table>/searchannotation_page/',methods=['POST'])
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
        raw_elasticsearch_query=data.get("raw_elasticsearch_query")
        resource_list = search_resource_annotation(resource_table, query, raw_elasticsearch_query=raw_elasticsearch_query,page=page,bookmark=bookmark)
    else:
        return jsonify(build_error_message("Error: No query field is provided. please specify an id."))
    return jsonify(resource_list)


@resources.route('/<resource_table>/searchannotation/',methods=['GET'])
def search_resource(resource_table):
    """
       This is the language searchengine API
       Call this api to test the /api/v1/resources/
       ---
       tags:
         - Searchengine  API
       parameters:
          - name: resource_table
            in: path
            type: string
            enum: ['image', 'project', 'screen', 'well']
            required: true
            default: all
          - name: data
            in: body
            required: true
            schema:
            id : query
            required:
              - first
              - last
            properties:
              first:
                type: string
                description: Unique identifier representing a First Name
              last:
                type: string
                description: Unique identifier representing a Last Name

       responses:
          200:
            description: A list of results
            examples:
              results: []
    """

    '''
               {'query': {'query_details': {'and_filters':
             [{'resource': 'image', 'name': 'HGNC Gene Symbol', 'value': 'pdx1', 'operator': 'equals', 'query_type': 'keyvalue'}], '
             or_filters': [], 'case_sensitive': False}, 'main_attributes': 
             {'or_main_attributes': []}}}
             
    

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
        print (data)
    except Exception as ex:
        return jsonify(build_error_message("Error: {error}".format(error="No proper query data is provided ")))

    if 'query' in data:
        query = data['query']
        #check if the app configuration will use ASYNCHRONOUS SEARCH or not.
        resource_list = search_resource_annotation(resource_table, query)
    else:
        return jsonify(build_error_message("Error: No query field is provided. please specify an id."))

    return jsonify(resource_list)

@resources.route('/<resource_table>/searchvalues/',methods=['GET'])
def get_values_using_value(resource_table):
    """
                    Search using part of value to find  attributes and values which contains the search term
                   ---
                   tags:
                     - Resource available attributes
                   parameters:
                      - name: resource_table
                        in: path
                        type: string
                        enum: ['image', 'project', 'screen', 'well', 'all']
                        required: true
                      - name: value
                        description: value search term
                        in: query
                        type: string
                        required: true

                   responses:
                      200:
                        description: A list of resource attributes
                        examples:
                          results: []

                """
    value=request.args.get("value")
    if not value:
        return jsonify(build_error_message("Error: {error}".format(error="No value is provided ")))
    #print (value, resource_table)
    return jsonify(search_value_for_resource(resource_table, value))
    #return json.dumps(query_cashed_bucket


@resources.route('/<resource_table>/searchvaluesusingkey/',methods=['GET'])
def search_values_for_a_key(resource_table):
    """
                Get the available attributes for one resource or all resources, return the available values along with the number of iamges which have it.
               ---
               tags:
                 - Resource available attributes
               parameters:
                  - name: resource_table
                    in: path
                    type: string
                    enum: ['image', 'project', 'screen', 'well', 'all']
                    required: true
                  - name: key
                    description: the resource attribute
                    in: query
                    type: string
                    required: true

               responses:
                  200:
                    description: A list of resource attributes
                    examples:
                      results: []

            """

    key=request.args.get("key")
    if not key:
        return jsonify(build_error_message("No key is provided "))


    return jsonify(query_cashed_bucket (key, resource_table))

@resources.route('/<resource_table>/getannotationkeys/',methods=['GET'])
def get_resource_keys(resource_table):
    """
            Query the available attributes for one resource or all resources
            and return a list which contains all the resource, value, bo of
           ---
           tags:
             - Resource available attributes
           parameters:
              - name: resource_table
                in: path
                type: string
                enum: ['image', 'project', 'screen', 'well', 'all']
                required: true
           responses:
              200:
                description: A list of resource attributes
                examples:
                  results: []

        """

    '''
     return the keys for a resource or all the resources
    '''
    resource_keys=get_resource_attributes(resource_table)
    return jsonify (resource_keys)


@resources.route('/<resource_table>/getannotationvalueskey/',methods=['GET'])
def get_resource_key_value(resource_table):
    """
          Query the available values for a resource attribute, returns only the values
           ---
           tags:
             - Values for a resource attribute
           parameters:
              - name: resource_table
                in: path
                type: string
                enum: ['image', 'project', 'screen', 'well']
                required: true
              - name: key
                description: the resource attribute
                in: query
                type: string
                required: true
           responses:
              200:
                description: A list of resource attributes
                examples:
                  results: []

        """
    '''
    get the values for a key for a specific resource
    '''
    key = request.args.get("key")
    if not key:
        return jsonify (build_error_message("No key is provided"))
    return jsonify(get_resource_attribute_values(resource_table, key))


@resources.route('/<resource_table>/getresourcenames/',methods=['GET'])
def get_resource_names_(resource_table):
    """
        Query the available  names attribute for a resource
       ---
       tags:
         - Resource available attributes
       parameters:
          - name: resource_table
            in: path
            type: string
            enum: ['project', 'screen']
            required: true
       responses:
          200:
            description: A list of resource attributes
            examples:
              results: []
    """
    '''
    Query the available attributes for a specific resource
    '''
    if not (get_resource_annotation_table(resource_table)):
        return ("NO data for table {table}".format(table=resource_table))

    names=get_resource_names(resource_table)
    return jsonify (names)

