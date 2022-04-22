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


@resources.route('/<resource_table>/searchannotation/',methods=['POST'])
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
                   Search using a part of or all of the value to find  attributes and values which contains the search term
                   ---
                   tags:
                     - Search for any value
                   parameters:
                      - name: resource_table
                        in: path
                        type: string
                        enum: ['image', 'project', 'screen', 'well', 'plate', 'all']
                        required: true
                      - name: value
                        description: search term
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
                Get the available values for an attribute for one or all resources.
               ---
               tags:
                 -  Available attributes for a resourse
               parameters:
                  - name: resource_table
                    in: path
                    type: string
                    enum: ['image', 'project', 'screen', 'well', 'plate', 'all']
                    required: true
                  - name: key
                    description: the resource attribute
                    in: query
                    type: string
                    required: true

               responses:
                  200:
                    description: A list of the available resource attribute values along with the number of items.
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
            Get the available attributes for one or all resources
           ---
           tags:
             -  Available attributes for a resource
           parameters:
              - name: resource_table
                in: path
                type: string
                enum: ['image', 'project', 'screen', 'well', 'plate', 'all']
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
          Get the available values for a resource attribute.
           ---
           tags:
             - Available values for a resource attribute
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
                description: A list of resource attribute values only.
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
        Get the available attribute names  for a resource
       ---
       tags:
         - Available names for a resource
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


@resources.route('/<resource_table>/submitquery/',methods=['POST', 'GET'])
def submit_query(resource_table):
    query =json.loads(request.data)
    if not query:
        return jsonify(build_error_message("No query is provided"))
    from search_engine.api.v1.resources.query_handler import determine_search_results_
    return jsonify(determine_search_results_(query))

@resources.route('/<resource_table>/search/',methods=['GET'])
def search(resource_table):
    """
              a searchengine endpoint to accept simple queries
           ---
           tags:
             - Single query

           parameters:
              - name: resource_table
                in: path
                type: string
                enum: ['image', 'project', 'screen', 'well', 'plate']
                required: true
              - name: key
                description: the resource attribute
                in: query
                type: string
                required: true
              - name: value
                description: the attribute value
                in: query
                type: string
                required: true
              - name: operator
                description: operator, default equals
                in: query
                type: string
                enum: ['equals', 'not_equals', 'contains', 'not_contains']
              - name: case_sensitive
                description: case sensitive query, default False
                in: query
                type: boolean
           responses:
              200:
                description: A list of resource attributes
                examples:
                  results: []
        """
    #?value=pdx1&&key=strain
    key = request.args.get("key")
    value = request.args.get("value")
    case_sensitive=request.args.get("case_sensitive")
    operator=request.args.get("operator")
    bookmark=request.args.get("bookmark")
    from search_engine.api.v1.resources.query_handler import simple_search
    results=simple_search(key, value, operator,case_sensitive,bookmark, resource_table)
    return jsonify(results)

    pass